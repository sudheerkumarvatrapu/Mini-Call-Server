#!/usr/bin/env python3
"""Serve a regression report with browser-safe evidence viewers."""

from __future__ import annotations

import argparse
import hashlib
import html
import os
import posixpath
import threading
import webbrowser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, unquote, urlsplit


TEXT_SUFFIXES = {
    ".call",
    ".csv",
    ".json",
    ".log",
    ".media",
    ".networking",
    ".platform",
    ".sip",
    ".sipp",
    ".stats",
    ".transcoding",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}


class EvidenceLinkRewriter(HTMLParser):
    """Rewrite relative evidence anchors to the browser-safe viewer route."""

    def __init__(self, document_path: str, evidence_paths: dict):
        super().__init__(convert_charrefs=False)
        self.document_path = document_path
        self.evidence_paths = evidence_paths
        self.parts = []

    def rewritten_href(self, value: str) -> str:
        parsed = urlsplit(value)
        if parsed.scheme or value.startswith(("#", "/evidence/")) or parsed.path.endswith(".html"):
            return value
        target = posixpath.normpath(posixpath.join(posixpath.dirname(self.document_path), parsed.path))
        relative = target.lstrip("/")
        token = hashlib.sha256(relative.encode("utf-8")).hexdigest()[:24]
        self.evidence_paths[token] = relative
        return f"/evidence/{token}"

    @staticmethod
    def attribute(name: str, value: Optional[str]) -> str:
        if value is None:
            return f" {name}"
        return f' {name}="{html.escape(value, quote=True)}"'

    def handle_starttag(self, tag: str, attrs) -> None:
        is_download = tag == "a" and any(name == "download" for name, _value in attrs)
        rendered = []
        for name, value in attrs:
            if tag == "a" and not is_download and name == "href" and value is not None:
                value = self.rewritten_href(value)
            rendered.append(self.attribute(name, value))
        self.parts.append(f"<{tag}{''.join(rendered)}>")

    def handle_startendtag(self, tag: str, attrs) -> None:
        rendered = "".join(self.attribute(name, value) for name, value in attrs)
        self.parts.append(f"<{tag}{rendered}/>")

    def handle_endtag(self, tag: str) -> None:
        self.parts.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_entityref(self, name: str) -> None:
        self.parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.parts.append(f"&#{name};")

    def handle_comment(self, data: str) -> None:
        self.parts.append(f"<!--{data}-->")

    def handle_decl(self, decl: str) -> None:
        self.parts.append(f"<!{decl}>")


def rewrite_report_links(source: str, document_path: str, evidence_paths: Optional[dict] = None) -> bytes:
    parser = EvidenceLinkRewriter(document_path, evidence_paths if evidence_paths is not None else {})
    parser.feed(source)
    parser.close()
    return "".join(parser.parts).encode("utf-8")


def human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size} B"


def page_shell(title: str, body: str) -> bytes:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{ color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }}
    body {{ margin: 0; color: #202b33; background: #f5f8fa; }}
    header {{ position: sticky; top: 0; padding: 14px 24px; background: #16324f; color: white; }}
    header a {{ color: #d9efff; text-decoration: none; margin-right: 18px; }}
    main {{ max-width: 1180px; margin: 20px auto; padding: 0 20px 40px; }}
    .meta {{ color: #5a6975; overflow-wrap: anywhere; }}
    pre {{ padding: 18px; border: 1px solid #c9d4dd; background: white; overflow: auto;
           white-space: pre-wrap; overflow-wrap: anywhere; font: 12px/1.5 SFMono-Regular, Consolas, monospace; }}
    code {{ padding: 2px 5px; background: #eaf2f8; border-radius: 3px; }}
  </style>
</head>
<body>
  <header><a href="/k8s-reports/latest.html">Back to report</a>{html.escape(title)}</header>
  <main>{body}</main>
</body>
</html>""".encode("utf-8")


def render_text_evidence(path: Path, root: Path) -> bytes:
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    relative = path.relative_to(root)
    body = (
        f'<p class="meta"><b>Evidence file:</b> {html.escape(str(relative))}<br>'
        f'<b>Size:</b> {human_size(len(raw))}</p>'
        f"<pre>{html.escape(text)}</pre>"
    )
    return page_shell(path.name, body)


def render_binary_evidence(path: Path, root: Path) -> bytes:
    size = path.stat().st_size
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    relative = path.relative_to(root)
    command = f'open -a Wireshark "{path}"'
    body = (
        f"<h1>{html.escape(path.name)}</h1>"
        f'<p class="meta"><b>Evidence file:</b> {html.escape(str(relative))}<br>'
        f'<b>Size:</b> {human_size(size)}<br><b>SHA-256:</b> {digest}</p>'
        "<p>This binary packet capture is retained unchanged. Open it in Wireshark:</p>"
        f"<pre>{html.escape(command)}</pre>"
    )
    return page_shell(path.name, body)


class EvidenceHandler(SimpleHTTPRequestHandler):
    server_version = "PlaySBCReport/1.0"

    def __init__(self, *args, directory: str, report_url: str, **kwargs):
        self.report_url = report_url
        super().__init__(*args, directory=directory, **kwargs)

    @property
    def evidence_root(self) -> Path:
        return Path(self.directory).resolve()

    def send_html(self, payload: bytes) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def safe_file(self, request_path: str) -> Optional[Path]:
        request_path = unquote(request_path).lstrip("/")
        candidate = (self.evidence_root / request_path).resolve()
        try:
            candidate.relative_to(self.evidence_root)
        except ValueError:
            return None
        return candidate

    def requested_file(self) -> Optional[Path]:
        return self.safe_file(urlsplit(self.path).path)

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urlsplit(self.path)
        if parsed.path == "/":
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", self.report_url)
            self.end_headers()
            return

        if parse_qs(parsed.query).get("raw") == ["1"]:
            path = self.requested_file()
            if path is None or not path.is_file():
                self.send_error(HTTPStatus.NOT_FOUND, "Evidence file was not found")
                return
            super().do_GET()
            return

        if parsed.path.startswith("/evidence/") or parsed.path == "/evidence":
            if parsed.path.startswith("/evidence/"):
                token = parsed.path.rsplit("/", 1)[-1]
            else:
                normalized = parse_qs(parsed.query).get("path", [""])[0]
                token = normalized.rsplit("/", 1)[-1] if normalized.startswith("evidence/") else ""
            relative = getattr(self.server, "evidence_paths", {}).get(token)
            path = self.safe_file(relative) if relative else None
            if path is None or not path.is_file():
                self.send_error(HTTPStatus.NOT_FOUND, "Evidence file was not found")
                return
            if path.suffix.lower() in TEXT_SUFFIXES:
                self.send_html(render_text_evidence(path, self.evidence_root))
            else:
                self.send_html(render_binary_evidence(path, self.evidence_root))
            return

        path = self.requested_file()
        if path is None:
            self.send_error(HTTPStatus.FORBIDDEN, "Evidence path is outside the run directory")
            return
        if path.is_file() and path.suffix.lower() == ".html":
            payload = rewrite_report_links(
                path.read_text(encoding="utf-8"),
                parsed.path,
                getattr(self.server, "evidence_paths", {}),
            )
            self.send_html(payload)
            return
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            self.send_html(render_text_evidence(path, self.evidence_root))
            return
        if path.is_file() and path.suffix.lower() in {".pcap", ".pcapng"}:
            self.send_html(render_binary_evidence(path, self.evidence_root))
            return
        super().do_GET()


def resolve_report(value: str) -> Path:
    report = Path(value).expanduser().resolve()
    if report.is_dir():
        report = report / "k8s-reports" / "latest.html"
    if not report.is_file():
        raise FileNotFoundError(f"Regression report not found: {report}")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", help="Path to latest.html or its regression run directory")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-open", action="store_true", help="Do not open the report in the default browser")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = resolve_report(args.report)
    root = report.parent.parent
    report_url = "/" + report.relative_to(root).as_posix()

    def handler(*handler_args, **handler_kwargs):
        return EvidenceHandler(
            *handler_args,
            directory=os.fspath(root),
            report_url=report_url,
            **handler_kwargs,
        )

    server = ThreadingHTTPServer((args.host, args.port), handler)
    server.evidence_paths = {}
    url = f"http://{args.host}:{args.port}{report_url}"
    print(f"PlaySBC regression report: {url}")
    print("Press Ctrl+C to stop the local evidence server.")
    if not args.no_open:
        threading.Timer(0.2, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping report server.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
