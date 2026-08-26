#!/usr/bin/env python3
"""Capture one manual real-device AKS call into a compact evidence bundle."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import signal
import shlex
import subprocess
import sys
import tarfile
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.real_device_evidence import write_evidence_bundle  # noqa: E402


DEFAULT_OUTPUT_ROOT = ROOT / "logs" / "Real-Device-Lab"
SIP_LOG_PATTERN = re.compile(
    r"SIP (?:INVITE|ACK|BYE|CANCEL)|SIP TX response|SIP response|INVITE ROUTE|"
    r"ROUTE FAILED|B2BUA|SDP SUMMARY|RTPENGINE|RTPengine",
    re.IGNORECASE,
)


@dataclass
class Capture:
    pod: str
    container: str
    remote_path: str
    local_path: Path
    process: subprocess.Popen[str]


def command_text(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def kubectl_command(args: argparse.Namespace, *parts: str) -> list[str]:
    command = [args.kubectl_bin]
    if args.context:
        command.extend(["--context", args.context])
    command.extend(parts)
    return command


def run_command(command: list[str], *, timeout: int = 60, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {command_text(command)}\n{result.stdout}{result.stderr}"
        )
    return result


def run_command_with_input(
    command: list[str],
    stdin: str,
    *,
    timeout: int = 60,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=ROOT, input=stdin, text=True, capture_output=True, timeout=timeout)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {command_text(command)}\n{result.stdout}{result.stderr}"
        )
    return result


def run_binary_command(
    command: list[str],
    *,
    timeout: int = 60,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=timeout)
    if check and result.returncode != 0:
        stdout = result.stdout.decode("utf-8", "replace")
        stderr = result.stderr.decode("utf-8", "replace")
        raise RuntimeError(
            f"Command failed ({result.returncode}): {command_text(command)}\n{stdout}{stderr}"
        )
    return result


def capture_filter(args: argparse.Namespace) -> str:
    sip_min = min(args.sip_port, args.tls_port, args.sip_capture_min)
    sip_max = max(args.sip_port, args.tls_port, args.sip_capture_max)
    return (
        f"((udp and (portrange {sip_min}-{sip_max} or port {args.rtpengine_control_port} "
        f"or portrange {args.rtp_min}-{args.rtp_max} or portrange {args.nodeport_min}-{args.nodeport_max})) "
        f"or (tcp and (portrange {sip_min}-{sip_max} or portrange {args.nodeport_min}-{args.nodeport_max})))"
    )


def capture_pod_manifest(args: argparse.Namespace, pod_name: str) -> dict[str, object]:
    return {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": pod_name,
            "namespace": args.namespace,
            "labels": {
                "app.kubernetes.io/name": "playsbc-real-device-capture",
                "app.kubernetes.io/instance": "playsbc",
                "app.kubernetes.io/part-of": "playsbc",
            },
        },
        "spec": {
            "restartPolicy": "Never",
            "hostNetwork": True,
            "dnsPolicy": "ClusterFirstWithHostNet",
            "terminationGracePeriodSeconds": 5,
            "tolerations": [{"operator": "Exists"}],
            "containers": [
                {
                    "name": "capture",
                    "image": args.capture_image,
                    "imagePullPolicy": args.capture_image_pull_policy,
                    "command": ["sh", "-lc"],
                    "args": ["trap 'exit 0' TERM INT; sleep 3600 & wait"],
                    "securityContext": {
                        "privileged": True,
                        "capabilities": {"add": ["NET_ADMIN", "NET_RAW"]},
                    },
                }
            ],
        },
    }


def create_capture_pod(args: argparse.Namespace, pod_name: str, bundle: Path) -> None:
    manifest = json.dumps(capture_pod_manifest(args, pod_name), indent=2)
    (bundle / "capture-pod.json").write_text(manifest + "\n", encoding="utf-8")
    result = run_command_with_input(
        kubectl_command(args, "apply", "-f", "-"),
        manifest,
        check=False,
    )
    (bundle / "capture-pod-apply.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"Could not create capture pod; see {bundle / 'capture-pod-apply.log'}")
    wait = run_command(
        kubectl_command(
            args,
            "-n",
            args.namespace,
            "wait",
            f"pod/{pod_name}",
            "--for=condition=Ready",
            f"--timeout={args.capture_pod_ready_timeout}s",
        ),
        timeout=args.capture_pod_ready_timeout + 15,
        check=False,
    )
    (bundle / "capture-pod-ready.log").write_text(wait.stdout + wait.stderr, encoding="utf-8")
    if wait.returncode != 0:
        describe = run_command(
            kubectl_command(args, "-n", args.namespace, "describe", "pod", pod_name),
            check=False,
        )
        (bundle / "capture-pod-describe.log").write_text(describe.stdout + describe.stderr, encoding="utf-8")
        raise RuntimeError(
            f"Capture pod did not become Ready; see {bundle / 'capture-pod-ready.log'} "
            f"and {bundle / 'capture-pod-describe.log'}"
        )


def delete_capture_pod(args: argparse.Namespace, pod_name: str, bundle: Path) -> None:
    if args.keep_capture_pod:
        return
    result = run_command(
        kubectl_command(
            args,
            "-n",
            args.namespace,
            "delete",
            "pod",
            pod_name,
            "--ignore-not-found=true",
            "--wait=false",
        ),
        check=False,
    )
    (bundle / "capture-pod-delete.log").write_text(result.stdout + result.stderr, encoding="utf-8")


def collect_cluster_snapshot(args: argparse.Namespace, bundle: Path, suffix: str) -> None:
    snapshots = {
        f"kubectl-pods-{suffix}.log": kubectl_command(
            args, "-n", args.namespace, "get", "pods", "-o", "wide"
        ),
        f"kubectl-services-{suffix}.log": kubectl_command(
            args, "-n", args.namespace, "get", "svc", "-o", "wide"
        ),
        f"kubectl-endpoints-{suffix}.log": kubectl_command(
            args, "-n", args.namespace, "get", "endpoints", "-o", "wide"
        ),
    }
    for file_name, command in snapshots.items():
        result = run_command(command, check=False)
        (bundle / file_name).write_text(result.stdout + result.stderr, encoding="utf-8")


def start_capture(args: argparse.Namespace, bundle: Path, pod: str) -> Capture:
    remote_path = "/tmp/playsbc-real-device-combined.pcap"
    local_path = bundle / "capture.pcap"
    tcpdump_filter = capture_filter(args)
    shell_command = (
        "command -v tcpdump >/dev/null 2>&1 || "
        "{ echo 'tcpdump not found in capture image; set --capture-image to an image that contains tcpdump' >&2; exit 127; }; "
        f"rm -f {shlex.quote(remote_path)}; "
        f"tcpdump -i any -U -n -s 0 -w {shlex.quote(remote_path)} {shlex.quote(tcpdump_filter)}"
    )
    command = kubectl_command(
        args,
        "-n",
        args.namespace,
        "exec",
        pod,
        "-c",
        "capture",
        "--",
        "sh",
        "-lc",
        shell_command,
    )
    (bundle / "tcpdump-command.txt").write_text(command_text(command) + "\n", encoding="utf-8")
    stdout = (bundle / "tcpdump.stdout.log").open("w", encoding="utf-8")
    stderr = (bundle / "tcpdump.stderr.log").open("w", encoding="utf-8")
    process = subprocess.Popen(command, cwd=ROOT, text=True, stdout=stdout, stderr=stderr)
    process._playsbc_stdout = stdout  # type: ignore[attr-defined]
    process._playsbc_stderr = stderr  # type: ignore[attr-defined]
    time.sleep(1.0)
    if process.poll() is not None:
        close_capture_files(process)
        raise RuntimeError(f"tcpdump exited early; see {bundle / 'tcpdump.stderr.log'}")
    return Capture(pod, "capture", remote_path, local_path, process)


def close_capture_files(process: subprocess.Popen[str]) -> None:
    stdout = getattr(process, "_playsbc_stdout", None)
    stderr = getattr(process, "_playsbc_stderr", None)
    for handle in (stdout, stderr):
        if handle:
            handle.close()


def stop_capture(args: argparse.Namespace, capture: Capture) -> None:
    if capture.process.poll() is None:
        run_command(
            kubectl_command(
                args,
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
            ),
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
        kubectl_command(
            args,
            "-n",
            args.namespace,
            "cp",
            f"{capture.pod}:{capture.remote_path}",
            str(capture.local_path),
            "-c",
            capture.container,
        ),
        check=False,
    )
    (bundle / "capture-copy.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode == 0 and capture.local_path.exists() and capture.local_path.stat().st_size > 24:
        return True

    fallback = run_binary_command(
        kubectl_command(
            args,
            "-n",
            args.namespace,
            "exec",
            capture.pod,
            "-c",
            capture.container,
            "--",
            "cat",
            capture.remote_path,
        ),
        check=False,
    )
    (bundle / "capture-copy-fallback.log").write_text(
        fallback.stderr.decode("utf-8", "replace"),
        encoding="utf-8",
    )
    if fallback.returncode == 0 and fallback.stdout:
        capture.local_path.write_bytes(fallback.stdout)
    return capture.local_path.exists() and capture.local_path.stat().st_size > 24


def collect_logs(args: argparse.Namespace, bundle: Path, capture_started_at: dt.datetime) -> None:
    since_time = capture_started_at.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    playsbc = run_command(
        kubectl_command(
            args,
            "-n",
            args.namespace,
            "logs",
            f"deployment/{args.playsbc_deployment}",
            f"--since-time={since_time}",
            "--timestamps=true",
        ),
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
        kubectl_command(
            args,
            "-n",
            args.namespace,
            "logs",
            f"deployment/{args.rtpengine_deployment}",
            f"--since-time={since_time}",
            "--timestamps=true",
        ),
        check=False,
    )
    (bundle / "rtpengine.log").write_text(rtpengine.stdout + rtpengine.stderr, encoding="utf-8")


def evidence_archive_path(args: argparse.Namespace, bundle: Path) -> Path | None:
    if args.archive_format == "none":
        return None
    suffix = ".zip" if args.archive_format == "zip" else ".tgz"
    return bundle.with_suffix(suffix)


def create_evidence_archive(args: argparse.Namespace, bundle: Path) -> Path | None:
    archive_path = evidence_archive_path(args, bundle)
    if archive_path is None:
        return None
    if archive_path.exists():
        archive_path.unlink()

    if args.archive_format == "zip":
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(bundle.rglob("*")):
                if path.is_file():
                    archive.write(path, Path(bundle.name) / path.relative_to(bundle))
        return archive_path

    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(bundle, arcname=bundle.name)
    return archive_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--namespace", default="playsbc")
    parser.add_argument("--kubectl-bin", default="kubectl")
    parser.add_argument(
        "--context",
        default="",
        help="Explicit kube context. Use this to keep AKS and kind captures isolated.",
    )
    parser.add_argument("--duration", type=int, default=90)
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--archive-format", choices=("tgz", "zip", "none"), default="tgz")
    parser.add_argument("--capture-image", default="nicolaka/netshoot:latest")
    parser.add_argument("--capture-image-pull-policy", default="IfNotPresent")
    parser.add_argument("--capture-pod-ready-timeout", type=int, default=120)
    parser.add_argument("--keep-capture-pod", action="store_true")
    parser.add_argument("--playsbc-selector", default="app.kubernetes.io/name=playsbc,app.kubernetes.io/instance=playsbc")
    parser.add_argument("--rtpengine-selector", default="app.kubernetes.io/name=playsbc-rtpengine,app.kubernetes.io/instance=playsbc")
    parser.add_argument("--playsbc-container", default="playsbc")
    parser.add_argument("--rtpengine-container", default="rtpengine")
    parser.add_argument("--playsbc-deployment", default="playsbc-playsbc")
    parser.add_argument("--rtpengine-deployment", default="playsbc-playsbc-rtpengine")
    parser.add_argument("--sip-port", type=int, default=5062)
    parser.add_argument("--tls-port", type=int, default=5061)
    parser.add_argument("--sip-capture-min", type=int, default=5060)
    parser.add_argument("--sip-capture-max", type=int, default=5079)
    parser.add_argument("--rtpengine-control-port", type=int, default=2223)
    parser.add_argument("--rtp-min", type=int, default=30000)
    parser.add_argument("--rtp-max", type=int, default=30049)
    parser.add_argument("--nodeport-min", type=int, default=30000)
    parser.add_argument("--nodeport-max", type=int, default=32767)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_id = time.strftime("real-device-capture-%Y%m%d-%H%M%S", time.localtime())
    bundle = Path(args.output_root) / run_id
    capture_pod = f"{run_id}-pod"
    bundle.mkdir(parents=True, exist_ok=True)
    (bundle / "README.txt").write_text(
        (
            "Place and clear the manual OBi1022 <-> Zoiper calls while this capture is running.\n"
            f"duration_seconds={args.duration}\n"
            f"kube_context={args.context or 'current'}\n"
            f"capture_pod={capture_pod}\n"
            f"capture_image={args.capture_image}\n"
            f"filter={capture_filter(args)}\n"
        ),
        encoding="utf-8",
    )

    capture: Capture | None = None
    copied = False
    capture_bytes = 0
    error = ""
    interrupted = False
    cleanup_interrupt_count = 0
    archive_path: Path | None = evidence_archive_path(args, bundle)
    archive_created = False
    archive_error = ""
    capture_started_at = dt.datetime.now(dt.timezone.utc)
    evidence_summary: dict[str, object] = {}
    try:
        collect_cluster_snapshot(args, bundle, "before")
        create_capture_pod(args, capture_pod, bundle)
        capture = start_capture(args, bundle, capture_pod)
        capture_started_at = dt.datetime.now(dt.timezone.utc)
        (bundle / "capture-window.log").write_text(
            f"capture_started_at={capture_started_at.isoformat().replace('+00:00', 'Z')}\n",
            encoding="utf-8",
        )
        print(f"Capturing for {args.duration}s using pod/{capture_pod}. Run the real device call now.")
        deadline = time.monotonic() + args.duration
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                time.sleep(min(1.0, remaining))
            except KeyboardInterrupt:
                interrupted = True
                print("Capture interrupted; finalizing evidence bundle now.", file=sys.stderr)
                break
    except KeyboardInterrupt:
        interrupted = True
        print("Capture interrupted; finalizing evidence bundle now.", file=sys.stderr)
    except Exception as exc:  # pragma: no cover - exercised against live AKS
        error = f"{type(exc).__name__}: {exc}"
        print(error, file=sys.stderr)
    finally:
        previous_sigint = signal.getsignal(signal.SIGINT)

        def defer_cleanup_interrupt(signum, frame):  # type: ignore[no-untyped-def]
            nonlocal cleanup_interrupt_count
            cleanup_interrupt_count += 1
            print("Cleanup is already saving evidence; please wait for the bundle path.", file=sys.stderr)

        signal.signal(signal.SIGINT, defer_cleanup_interrupt)
        try:
            if capture is not None:
                stop_capture(args, capture)
                copied = copy_capture(args, capture, bundle)
                capture_bytes = capture.local_path.stat().st_size if copied else 0
            collect_cluster_snapshot(args, bundle, "after")
            collect_logs(args, bundle, capture_started_at)
            if copied:
                evidence_summary = write_evidence_bundle(
                    bundle,
                    rtp_min=args.rtp_min,
                    rtp_max=args.rtp_max,
                )
            delete_capture_pod(args, capture_pod, bundle)
        except Exception as exc:  # pragma: no cover - exercised against live AKS
            if not error:
                error = f"{type(exc).__name__}: {exc}"
            print(error, file=sys.stderr)
        finally:
            signal.signal(signal.SIGINT, previous_sigint)

        if archive_path is not None:
            try:
                created_archive = create_evidence_archive(args, bundle)
                archive_created = bool(created_archive and created_archive.exists())
            except Exception as exc:  # pragma: no cover - exercised against live AKS
                archive_error = f"{type(exc).__name__}: {exc}"
                if not error:
                    error = archive_error
                print(archive_error, file=sys.stderr)

        (bundle / "summary.log").write_text(
            (
                f"bundle={bundle}\n"
                f"archive={archive_path or 'none'}\n"
                f"archive_format={args.archive_format}\n"
                f"archive_created={str(archive_created).lower()}\n"
                f"archive_error={archive_error or 'none'}\n"
                f"capture_pcap={bundle / 'capture.pcap'}\n"
                f"capture_source=single_host_network_capture_pod\n"
                f"kube_context={args.context or 'current'}\n"
                f"capture_pod={capture_pod}\n"
                f"capture_image={args.capture_image}\n"
                f"capture_bytes={capture_bytes}\n"
                f"single_combined_pcap={str(copied and capture_bytes > 24).lower()}\n"
                f"canonical_sip_events={evidence_summary.get('sip', {}).get('canonical_events', 0)}\n"
                f"capture_mirror_packets={evidence_summary.get('sip', {}).get('capture_mirror_packets', 0)}\n"
                f"sip_retransmitted_packets={evidence_summary.get('sip', {}).get('retransmitted_packets', 0)}\n"
                f"voice_rtp_packets={evidence_summary.get('media', {}).get('packet_counts', {}).get('voice_rtp', 0)}\n"
                f"rtcp_status={evidence_summary.get('media', {}).get('rtcp_status', 'not-analyzed')}\n"
                f"bidirectional_rtp_proven={str(evidence_summary.get('media', {}).get('bidirectional_rtp_proven', False)).lower()}\n"
                f"interrupted={str(interrupted).lower()}\n"
                f"cleanup_interrupt_count={cleanup_interrupt_count}\n"
                f"error={error or 'none'}\n"
            ),
            encoding="utf-8",
        )
        if archive_created and archive_path is not None:
            try:
                create_evidence_archive(args, bundle)
            except Exception as exc:  # pragma: no cover - exercised against live AKS
                print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
    print(f"Real-device evidence bundle: {bundle}")
    if archive_created and archive_path is not None:
        print(f"Real-device evidence archive: {archive_path}")
    return 0 if not error and copied and capture_bytes > 24 else 1


if __name__ == "__main__":
    raise SystemExit(main())
