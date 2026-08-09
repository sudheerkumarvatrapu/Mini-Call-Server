#!/usr/bin/env python3
"""Capture one manual real-device AKS call into a compact evidence bundle."""

from __future__ import annotations

import argparse
import re
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.run_k8s_regression import merge_pcap_files, prune_merged_capture_inputs  # noqa: E402


DEFAULT_OUTPUT_ROOT = ROOT / "logs" / "Real-Device-Lab"
SIP_LOG_PATTERN = re.compile(
    r"SIP (?:INVITE|ACK|BYE|CANCEL)|SIP TX response|SIP response|INVITE ROUTE|"
    r"ROUTE FAILED|B2BUA|SDP SUMMARY|RTPENGINE|RTPengine",
    re.IGNORECASE,
)


@dataclass
class Capture:
    role: str
    pod: str
    container: str
    remote_path: str
    local_path: Path
    process: subprocess.Popen[str]


def command_text(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def run_command(command: list[str], *, timeout: int = 60, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {command_text(command)}\n{result.stdout}{result.stderr}"
        )
    return result


def capture_filter(args: argparse.Namespace) -> str:
    return (
        f"((udp and (port {args.sip_port} or portrange {args.rtp_min}-{args.rtp_max})) "
        f"or (tcp and (port {args.sip_port} or port {args.tls_port})))"
    )


def first_pod(args: argparse.Namespace, selector: str) -> str:
    result = run_command(
        [
            args.kubectl_bin,
            "-n",
            args.namespace,
            "get",
            "pods",
            "-l",
            selector,
            "-o",
            "jsonpath={.items[0].metadata.name}",
        ]
    )
    pod = result.stdout.strip()
    if not pod:
        raise RuntimeError(f"No pod found for selector={selector}")
    return pod


def start_capture(args: argparse.Namespace, bundle: Path, role: str, pod: str, container: str) -> Capture:
    remote_path = f"/tmp/playsbc-real-device-{role}.pcap"
    local_path = bundle / f"capture-{role}.pcap"
    step_dir = bundle / f"capture-{role}"
    step_dir.mkdir(parents=True, exist_ok=True)
    tcpdump_filter = capture_filter(args)
    shell_command = (
        f"rm -f {shlex.quote(remote_path)}; "
        f"tcpdump -i any -U -n -s 0 -w {shlex.quote(remote_path)} {shlex.quote(tcpdump_filter)}"
    )
    command = [
        args.kubectl_bin,
        "-n",
        args.namespace,
        "exec",
        pod,
        "-c",
        container,
        "--",
        "sh",
        "-lc",
        shell_command,
    ]
    (step_dir / "command.txt").write_text(command_text(command) + "\n", encoding="utf-8")
    stdout = (step_dir / "stdout.log").open("w", encoding="utf-8")
    stderr = (step_dir / "stderr.log").open("w", encoding="utf-8")
    process = subprocess.Popen(command, cwd=ROOT, text=True, stdout=stdout, stderr=stderr)
    process._playsbc_stdout = stdout  # type: ignore[attr-defined]
    process._playsbc_stderr = stderr  # type: ignore[attr-defined]
    time.sleep(1.0)
    if process.poll() is not None:
        close_capture_files(process)
        raise RuntimeError(f"tcpdump exited early for role={role}; see {step_dir}")
    return Capture(role, pod, container, remote_path, local_path, process)


def close_capture_files(process: subprocess.Popen[str]) -> None:
    stdout = getattr(process, "_playsbc_stdout", None)
    stderr = getattr(process, "_playsbc_stderr", None)
    for handle in (stdout, stderr):
        if handle:
            handle.close()


def stop_capture(args: argparse.Namespace, capture: Capture) -> None:
    if capture.process.poll() is None:
        run_command(
            [
                args.kubectl_bin,
                "-n",
                args.namespace,
                "exec",
                capture.pod,
                "-c",
                capture.container,
                "--",
                "sh",
                "-lc",
                "pkill -INT tcpdump || true",
            ],
            check=False,
        )
        capture.process.terminate()
        try:
            capture.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            capture.process.kill()
            capture.process.wait(timeout=5)
    close_capture_files(capture.process)


def copy_capture(args: argparse.Namespace, capture: Capture, bundle: Path) -> bool:
    result = run_command(
        [
            args.kubectl_bin,
            "-n",
            args.namespace,
            "cp",
            f"{capture.pod}:{capture.remote_path}",
            str(capture.local_path),
            "-c",
            capture.container,
        ],
        check=False,
    )
    (bundle / f"capture-{capture.role}" / "copy.log").write_text(
        result.stdout + result.stderr,
        encoding="utf-8",
    )
    return result.returncode == 0 and capture.local_path.exists() and capture.local_path.stat().st_size > 24


def collect_logs(args: argparse.Namespace, bundle: Path) -> None:
    since = f"{max(int(args.duration) + 90, 180)}s"
    playsbc = run_command(
        [
            args.kubectl_bin,
            "-n",
            args.namespace,
            "logs",
            f"deployment/{args.playsbc_deployment}",
            f"--since={since}",
        ],
        check=False,
    )
    playsbc_text = playsbc.stdout + playsbc.stderr
    (bundle / "playsbc.log").write_text(playsbc_text, encoding="utf-8")
    sip_lines = [line for line in playsbc_text.splitlines() if SIP_LOG_PATTERN.search(line)]
    (bundle / "sipmsg.log").write_text(
        "PLAY SBC REAL DEVICE SIP/RTP TRACE\n" + "\n".join(sip_lines).rstrip() + "\n",
        encoding="utf-8",
    )
    verdict_lines = [line for line in playsbc_text.splitlines() if "RTPENGINE PACKET VERDICT" in line]
    (bundle / "rtpengine-verdict.log").write_text("\n".join(verdict_lines).rstrip() + "\n", encoding="utf-8")
    rtpengine = run_command(
        [
            args.kubectl_bin,
            "-n",
            args.namespace,
            "logs",
            f"deployment/{args.rtpengine_deployment}",
            f"--since={since}",
        ],
        check=False,
    )
    (bundle / "rtpengine.log").write_text(rtpengine.stdout + rtpengine.stderr, encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--namespace", default="playsbc")
    parser.add_argument("--kubectl-bin", default="kubectl")
    parser.add_argument("--duration", type=int, default=90)
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--playsbc-selector", default="app.kubernetes.io/name=playsbc,app.kubernetes.io/instance=playsbc")
    parser.add_argument("--rtpengine-selector", default="app.kubernetes.io/name=playsbc-rtpengine,app.kubernetes.io/instance=playsbc")
    parser.add_argument("--playsbc-container", default="playsbc")
    parser.add_argument("--rtpengine-container", default="rtpengine")
    parser.add_argument("--playsbc-deployment", default="playsbc-playsbc")
    parser.add_argument("--rtpengine-deployment", default="playsbc-playsbc-rtpengine")
    parser.add_argument("--sip-port", type=int, default=5062)
    parser.add_argument("--tls-port", type=int, default=5061)
    parser.add_argument("--rtp-min", type=int, default=30000)
    parser.add_argument("--rtp-max", type=int, default=30049)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_id = time.strftime("real-device-capture-%Y%m%d-%H%M%S", time.localtime())
    bundle = Path(args.output_root) / run_id
    bundle.mkdir(parents=True, exist_ok=True)
    (bundle / "README.txt").write_text(
        (
            "Place and clear the manual OBi1022 <-> Zoiper calls while this capture is running.\n"
            f"duration_seconds={args.duration}\n"
            f"filter={capture_filter(args)}\n"
        ),
        encoding="utf-8",
    )

    captures: list[Capture] = []
    try:
        captures.append(
            start_capture(
                args,
                bundle,
                "playsbc",
                first_pod(args, args.playsbc_selector),
                args.playsbc_container,
            )
        )
        captures.append(
            start_capture(
                args,
                bundle,
                "rtpengine",
                first_pod(args, args.rtpengine_selector),
                args.rtpengine_container,
            )
        )
        print(f"Capturing for {args.duration}s. Run the real device call now.")
        time.sleep(args.duration)
    finally:
        for capture in captures:
            stop_capture(args, capture)

    copied = [capture.local_path for capture in captures if copy_capture(args, capture, bundle)]
    merged_bytes = merge_pcap_files(copied, bundle / "capture.pcap")
    removed = prune_merged_capture_inputs(copied, bundle / "capture.pcap") if merged_bytes > 0 else []
    collect_logs(args, bundle)
    (bundle / "summary.log").write_text(
        (
            f"bundle={bundle}\n"
            f"capture_pcap={bundle / 'capture.pcap'}\n"
            f"merged_sources={','.join(path.name for path in copied) or 'none'}\n"
            f"discarded_role_pcaps={','.join(removed) or 'none'}\n"
            f"merged_bytes={merged_bytes}\n"
        ),
        encoding="utf-8",
    )
    print(f"Real-device evidence bundle: {bundle}")
    return 0 if merged_bytes > 24 else 1


if __name__ == "__main__":
    raise SystemExit(main())
