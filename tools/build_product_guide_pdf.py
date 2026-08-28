#!/usr/bin/env python3
"""Build the PlaySBC product and administration guide PDF."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    Image,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "docs" / "PRODUCT_GUIDE.md"
DEFAULT_OUTPUT = ROOT / "output" / "pdf" / "PlaySBC-v2.6.0-Product-Guide.pdf"
LOGO = ROOT / "docs" / "assets" / "playsbc-logo-corporate-mediaflow.png"

NAVY = colors.HexColor("#16324F")
BLUE = colors.HexColor("#2166A5")
CYAN = colors.HexColor("#2A9D8F")
GREEN = colors.HexColor("#4D8B62")
ORANGE = colors.HexColor("#D9822B")
RED = colors.HexColor("#B5473C")
INK = colors.HexColor("#202B33")
MUTED = colors.HexColor("#5A6975")
LINE = colors.HexColor("#C9D4DD")
PALE = colors.HexColor("#F5F8FA")
PALE_BLUE = colors.HexColor("#EAF2F8")
WHITE = colors.white


def escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def inline_markup(text: str) -> str:
    text = escape(text.strip())
    text = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return text


class GuideDocTemplate(BaseDocTemplate):
    def afterFlowable(self, flowable):  # noqa: N802 - ReportLab API
        if not isinstance(flowable, Paragraph):
            return
        level = getattr(flowable, "toc_level", None)
        if level is None:
            return
        text = flowable.getPlainText()
        key = f"heading-{level}-{self.seq.nextf('heading')}"
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(text, key, level=level, closed=False)
        self.notify("TOCEntry", (level, text, self.page, key))


class Diagram(Flowable):
    def __init__(self, diagram_type: str, width: float, height: float = 68 * mm):
        super().__init__()
        self.diagram_type = diagram_type
        self.width = width
        self.height = height

    def _box(self, canvas, x, y, w, h, title, subtitle="", fill=WHITE, stroke=LINE):
        canvas.setFillColor(fill)
        canvas.setStrokeColor(stroke)
        canvas.setLineWidth(0.8)
        canvas.roundRect(x, y, w, h, 4, fill=1, stroke=1)
        canvas.setFillColor(INK)
        canvas.setFont("Helvetica-Bold", 8.5)
        canvas.drawCentredString(x + w / 2, y + h - 12, title)
        if subtitle:
            canvas.setFillColor(MUTED)
            canvas.setFont("Helvetica", 6.7)
            for index, line in enumerate(subtitle.split("\n")[:3]):
                canvas.drawCentredString(x + w / 2, y + h - 23 - index * 8, line)

    def _arrow(self, canvas, x1, y1, x2, y2, label="", color=BLUE):
        canvas.setStrokeColor(color)
        canvas.setFillColor(color)
        canvas.setLineWidth(1.2)
        canvas.line(x1, y1, x2, y2)
        angle = 4
        if abs(x2 - x1) >= abs(y2 - y1):
            direction = 1 if x2 > x1 else -1
            canvas.line(x2, y2, x2 - direction * 7, y2 + angle)
            canvas.line(x2, y2, x2 - direction * 7, y2 - angle)
        else:
            direction = 1 if y2 > y1 else -1
            canvas.line(x2, y2, x2 + angle, y2 - direction * 7)
            canvas.line(x2, y2, x2 - angle, y2 - direction * 7)
        if label:
            canvas.setFillColor(MUTED)
            canvas.setFont("Helvetica", 6.4)
            canvas.drawCentredString((x1 + x2) / 2, (y1 + y2) / 2 + 5, label)

    def _title(self, canvas, title, subtitle):
        canvas.setFillColor(NAVY)
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(0, self.height - 13, title)
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica", 7.2)
        canvas.drawString(0, self.height - 25, subtitle)
        canvas.setStrokeColor(LINE)
        canvas.line(0, self.height - 31, self.width, self.height - 31)

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        draw = getattr(self, f"_draw_{self.diagram_type}")
        draw(canvas)
        canvas.restoreState()

    def _draw_architecture(self, c):
        self._title(c, "PlaySBC component architecture", "Signalling, media, orchestration, and telemetry remain independently observable")
        y = 50
        h = 48
        w = 78
        gap = 18
        x0 = 4
        boxes = [
            ("Core endpoints", "SIPp / devices", PALE_BLUE),
            ("PlaySBC", "Registrar + B2BUA\npolicy + metrics", colors.HexColor("#E8F0F7")),
            ("RTPengine", "RTP/RTCP + SRTP\nNAT + transcoding", colors.HexColor("#E8F5F2")),
            ("Peer / AI", "SIPp / devices\nRasa route", colors.HexColor("#F4F0E8")),
        ]
        for index, (title, subtitle, fill) in enumerate(boxes):
            x = x0 + index * (w + gap)
            self._box(c, x, y, w, h, title, subtitle, fill)
            if index:
                self._arrow(c, x - gap + 2, y + h / 2, x - 2, y + h / 2, "SIP" if index != 2 else "NG")
        self._box(c, 112, 4, 90, 32, "Regression runner", "Profiles + evidence", PALE)
        self._box(c, 224, 4, 90, 32, "Prometheus / Grafana", "Metrics + dashboards", PALE)
        self._arrow(c, 157, 36, 157, 49, "control")
        self._arrow(c, 269, 36, 269, 49, "scrape")

    def _draw_docker(self, c):
        self._title(c, "Docker process and topology lane", "Fast development checks with isolated core and peer container networks")
        self._box(c, 6, 52, 78, 46, "Core SIPp", "172.28.0.10", PALE_BLUE)
        self._box(c, 106, 52, 82, 46, "PlaySBC", "172.28.0.20\nB2BUA", colors.HexColor("#E8F0F7"))
        self._box(c, 210, 52, 82, 46, "RTPengine", "172.28.0.40\n192.168.28.40", colors.HexColor("#E8F5F2"))
        self._box(c, 314, 52, 78, 46, "Peer SIPp", "192.168.28.30", colors.HexColor("#F4F0E8"))
        self._arrow(c, 84, 75, 104, 75, "SIP")
        self._arrow(c, 188, 75, 208, 75, "NG")
        self._arrow(c, 292, 75, 312, 75, "RTP/RTCP")
        self._box(c, 106, 5, 186, 28, "Host output", "HTML + logs + combined PCAP", PALE)
        self._arrow(c, 199, 34, 199, 51, "evidence")

    def _draw_kind(self, c):
        self._title(c, "Canonical kind regression lane", "One Docker-backed Kubernetes node, two active-active signalling/media replicas")
        self._box(c, 6, 61, 74, 40, "Regression Job", "70 profiles", PALE)
        self._box(c, 99, 66, 76, 35, "SIPp core", "temporary pod", PALE_BLUE)
        self._box(c, 99, 20, 76, 35, "SIPp peer", "temporary pod", colors.HexColor("#F4F0E8"))
        self._box(c, 197, 61, 84, 40, "PlaySBC 0 / 1", "StatefulSet\nshared lab state", colors.HexColor("#E8F0F7"))
        self._box(c, 303, 61, 84, 40, "RTPengine 0 / 1", "StatefulSet\npaired media", colors.HexColor("#E8F5F2"))
        self._box(c, 221, 8, 142, 32, "Prometheus + Grafana", "metrics and dashboards", PALE)
        self._arrow(c, 80, 81, 97, 81, "create")
        self._arrow(c, 175, 83, 195, 83, "SIP")
        self._arrow(c, 175, 38, 238, 60, "SIP")
        self._arrow(c, 281, 81, 301, 81, "NG")
        self._arrow(c, 292, 40, 292, 60, "scrape")

    def _draw_minikube(self, c):
        self._title(c, "Minikube compatibility lane", "Portable chart validation; kind remains the canonical full-regression environment")
        self._box(c, 18, 56, 92, 44, "Host runtime", "Docker driver or VM", PALE)
        self._box(c, 140, 56, 96, 44, "Minikube node", "PlaySBC + RTPengine", colors.HexColor("#E8F0F7"))
        self._box(c, 266, 56, 110, 44, "NodePort / tunnel", "lab-only exposure", colors.HexColor("#E8F5F2"))
        self._box(c, 140, 8, 96, 30, "Compatibility run", "selected or full profiles", PALE_BLUE)
        self._arrow(c, 110, 78, 138, 78, "runtime")
        self._arrow(c, 236, 78, 264, 78, "service")
        self._arrow(c, 188, 39, 188, 55, "test")

    def _draw_kubernetes(self, c):
        self._title(c, "Generic Helm-managed Kubernetes", "Operator supplies storage, exposure, identity, and network policy appropriate to the platform")
        self._box(c, 6, 60, 86, 42, "SIP clients", "UDP / TCP / TLS", PALE_BLUE)
        self._box(c, 112, 60, 88, 42, "SIP service", "LB or private VIP", PALE)
        self._box(c, 220, 60, 80, 42, "PlaySBC", "Deployment or STS", colors.HexColor("#E8F0F7"))
        self._box(c, 320, 60, 76, 42, "RTPengine", "media service", colors.HexColor("#E8F5F2"))
        self._box(c, 112, 8, 88, 30, "Storage / secrets", "platform-owned", PALE)
        self._box(c, 220, 8, 176, 30, "Prometheus / Grafana", "optional observability", PALE)
        self._arrow(c, 92, 81, 110, 81, "SIP")
        self._arrow(c, 200, 81, 218, 81, "SIP")
        self._arrow(c, 300, 81, 318, 81, "NG")
        self._arrow(c, 156, 39, 244, 59, "state")
        self._arrow(c, 308, 39, 308, 59, "metrics")

    def _draw_aks(self, c):
        self._title(c, "Azure AKS public lab", "Separate static SIP and RTP addresses; managed identity controls Network RG resources")
        self._box(c, 2, 67, 72, 38, "Internet devices", "OBi / Zoiper / SIPp", PALE_BLUE)
        self._box(c, 91, 76, 78, 31, "SIP static IP", "Azure LB :5061/5062", PALE)
        self._box(c, 91, 34, 78, 31, "RTP static IP", "Azure LB :30000-30049", PALE)
        self._box(c, 190, 67, 82, 38, "PlaySBC pods", "SIP + B2BUA", colors.HexColor("#E8F0F7"))
        self._box(c, 190, 22, 82, 38, "RTPengine pods", "RTP/RTCP + NAT", colors.HexColor("#E8F5F2"))
        self._box(c, 294, 67, 96, 38, "ACR", "4 versioned images", colors.HexColor("#F4F0E8"))
        self._box(c, 294, 22, 96, 38, "Prometheus / Grafana", "cluster observability", PALE)
        self._arrow(c, 74, 86, 89, 91, "SIP")
        self._arrow(c, 74, 78, 89, 49, "RTP")
        self._arrow(c, 169, 91, 188, 86, "SIP")
        self._arrow(c, 169, 49, 188, 42, "media")
        self._arrow(c, 294, 86, 274, 86, "pull", ORANGE)
        self._arrow(c, 294, 42, 274, 42, "scrape", GREEN)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 6.5)
        c.drawCentredString(241, 8, "AKS identity -> Network Contributor on the network resource group")

    def _draw_real_device(self, c):
        self._title(c, "Local kind real-device lane", "Dedicated cluster exposes the Mac LAN address; never reuse the regression cluster")
        self._box(c, 4, 58, 80, 44, "OBi1022", "1001 / UDP", PALE_BLUE)
        self._box(c, 4, 9, 80, 38, "Zoiper", "1002 / UDP", colors.HexColor("#F4F0E8"))
        self._box(c, 112, 58, 88, 44, "Mac LAN IP", "5061/5062\n30000-30049", PALE)
        self._box(c, 228, 58, 76, 44, "PlaySBC", "host network", colors.HexColor("#E8F0F7"))
        self._box(c, 332, 58, 66, 44, "RTPengine", "host network", colors.HexColor("#E8F5F2"))
        self._box(c, 228, 9, 170, 30, "Evidence capture pod", "combined SIP + RTP + RTCP + network PCAP", PALE)
        self._arrow(c, 84, 80, 110, 80, "LAN")
        self._arrow(c, 84, 28, 140, 57, "LAN")
        self._arrow(c, 200, 80, 226, 80, "SIP")
        self._arrow(c, 304, 80, 330, 80, "NG")
        self._arrow(c, 313, 40, 313, 57, "capture")


def styles():
    sample = getSampleStyleSheet()
    return {
        "body": ParagraphStyle(
            "GuideBody",
            parent=sample["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12.4,
            textColor=INK,
            spaceAfter=5,
        ),
        "small": ParagraphStyle(
            "GuideSmall",
            parent=sample["BodyText"],
            fontName="Helvetica",
            fontSize=7.4,
            leading=9.6,
            textColor=MUTED,
        ),
        "h1": ParagraphStyle(
            "GuideH1",
            parent=sample["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=19,
            leading=23,
            textColor=NAVY,
            spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "GuideH2",
            parent=sample["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=BLUE,
            spaceBefore=8,
            spaceAfter=6,
        ),
        "h3": ParagraphStyle(
            "GuideH3",
            parent=sample["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13,
            textColor=NAVY,
            spaceBefore=6,
            spaceAfter=4,
        ),
        "bullet": ParagraphStyle(
            "GuideBullet",
            parent=sample["BodyText"],
            fontName="Helvetica",
            fontSize=8.8,
            leading=11.8,
            leftIndent=12,
            firstLineIndent=-7,
            textColor=INK,
            spaceAfter=2,
        ),
        "code": ParagraphStyle(
            "GuideCode",
            fontName="Courier",
            fontSize=6.6,
            leading=8.2,
            textColor=INK,
            leftIndent=0,
            rightIndent=0,
            spaceBefore=0,
            spaceAfter=0,
        ),
        "toc": ParagraphStyle(
            "GuideTOC",
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=INK,
            leftIndent=12,
            firstLineIndent=-12,
        ),
    }


def make_heading(text: str, level: int, style_map):
    paragraph = Paragraph(inline_markup(text), style_map[f"h{level}"])
    paragraph.toc_level = level - 1
    return paragraph


def code_block(text: str, style_map, available_width: float):
    max_length = max((len(line) for line in text.splitlines()), default=1)
    style = style_map["code"].clone("GuideCodeDynamic")
    if max_length > 102:
        style.fontSize = max(5.5, 6.6 * 102 / max_length)
        style.leading = max(7.0, style.fontSize + 1.5)
    content = Preformatted(text.rstrip(), style)
    table = Table([[content]], colWidths=[available_width], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALE),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("LINEBEFORE", (0, 0), (0, -1), 2.2, BLUE),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return [Spacer(1, 3), table, Spacer(1, 7)]


def markdown_table(lines: list[str], style_map, available_width: float):
    rows = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        rows.append(cells)
    if len(rows) > 1 and all(set(cell) <= {"-", ":"} for cell in rows[1]):
        rows.pop(1)
    columns = max(len(row) for row in rows)
    normalized = [row + [""] * (columns - len(row)) for row in rows]
    data = []
    for row_index, row in enumerate(normalized):
        style = style_map["small"].clone(f"TableRow{row_index}")
        if row_index == 0:
            style.fontName = "Helvetica-Bold"
            style.textColor = WHITE
        data.append([Paragraph(inline_markup(cell), style) for cell in row])
    widths = [available_width / columns] * columns
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("BACKGROUND", (0, 1), (-1, -1), WHITE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PALE]),
                ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return [Spacer(1, 3), table, Spacer(1, 7)]


def parse_markdown(source: str, style_map, available_width: float):
    lines = source.splitlines()
    story = []
    paragraph = []
    index = 0
    first_h1 = True

    def flush_paragraph():
        if paragraph:
            story.append(Paragraph(inline_markup(" ".join(paragraph)), style_map["body"]))
            paragraph.clear()

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_paragraph()
            index += 1
            code_lines = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            story.extend(code_block("\n".join(code_lines), style_map, available_width))
        elif stripped.startswith("[[") and stripped.endswith("]]" ):
            flush_paragraph()
            mapping = {
                "[[ARCHITECTURE_DIAGRAM]]": "architecture",
                "[[DOCKER_DIAGRAM]]": "docker",
                "[[KIND_DIAGRAM]]": "kind",
                "[[MINIKUBE_DIAGRAM]]": "minikube",
                "[[KUBERNETES_DIAGRAM]]": "kubernetes",
                "[[AKS_DIAGRAM]]": "aks",
                "[[REAL_DEVICE_DIAGRAM]]": "real_device",
            }
            if stripped in mapping:
                story.extend([Spacer(1, 4), Diagram(mapping[stripped], available_width), Spacer(1, 8)])
        elif stripped.startswith("# "):
            flush_paragraph()
            if not first_h1:
                story.append(PageBreak())
            first_h1 = False
            story.append(make_heading(stripped[2:], 1, style_map))
        elif stripped.startswith("## "):
            flush_paragraph()
            story.append(make_heading(stripped[3:], 2, style_map))
        elif stripped.startswith("### "):
            flush_paragraph()
            story.append(make_heading(stripped[4:], 3, style_map))
        elif stripped.startswith("| "):
            flush_paragraph()
            table_lines = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index])
                index += 1
            index -= 1
            story.extend(markdown_table(table_lines, style_map, available_width))
        elif re.match(r"^[-*] ", stripped):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped[2:]), style_map["bullet"], bulletText="-"))
        elif re.match(r"^\d+\. ", stripped):
            flush_paragraph()
            number, content = stripped.split(". ", 1)
            story.append(Paragraph(inline_markup(content), style_map["bullet"], bulletText=f"{number}."))
        elif not stripped:
            flush_paragraph()
            story.append(Spacer(1, 2))
        else:
            paragraph.append(stripped)
        index += 1
    flush_paragraph()
    return story


def cover(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(WHITE)
    canvas.rect(0, 0, width, height, fill=1, stroke=0)
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, 13 * mm, height, fill=1, stroke=0)
    canvas.setFillColor(CYAN)
    canvas.rect(13 * mm, 0, 3 * mm, height, fill=1, stroke=0)
    canvas.restoreState()


def later_page(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(20 * mm, height - 16 * mm, width - 20 * mm, height - 16 * mm)
    canvas.setFillColor(NAVY)
    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.drawString(20 * mm, height - 12.5 * mm, "PlaySBC v2.6.0 Product Guide")
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7)
    canvas.drawRightString(width - 20 * mm, height - 12.5 * mm, "Final public MIT engineering baseline")
    canvas.setStrokeColor(LINE)
    canvas.line(20 * mm, 14 * mm, width - 20 * mm, 14 * mm)
    canvas.setFillColor(MUTED)
    canvas.drawString(20 * mm, 9.5 * mm, "Contributor: Sudheer Kumar Vatrapu")
    canvas.drawRightString(width - 20 * mm, 9.5 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build(source_path: Path, output_path: Path):
    style_map = styles()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    width, height = A4
    margin_x = 20 * mm
    frame_width = width - 2 * margin_x
    frame_height = height - 36 * mm

    doc = GuideDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=margin_x,
        rightMargin=margin_x,
        topMargin=19 * mm,
        bottomMargin=17 * mm,
        title="PlaySBC v2.6.0 Product Guide",
        author="Sudheer Kumar Vatrapu",
        subject="Features, architecture, and administration guide",
    )
    cover_frame = Frame(25 * mm, 18 * mm, width - 45 * mm, height - 36 * mm, id="cover", showBoundary=0)
    body_frame = Frame(margin_x, 17 * mm, frame_width, frame_height, id="body", showBoundary=0)
    doc.addPageTemplates(
        [
            PageTemplate(id="Cover", frames=[cover_frame], onPage=cover),
            PageTemplate(id="Body", frames=[body_frame], onPage=later_page),
        ]
    )

    story = []
    if LOGO.exists():
        logo = Image(str(LOGO), width=126 * mm, height=38 * mm, kind="proportional")
        logo.hAlign = "LEFT"
        story.extend([Spacer(1, 48 * mm), logo, Spacer(1, 13 * mm)])
    title_style = ParagraphStyle(
        "CoverTitle",
        fontName="Helvetica-Bold",
        fontSize=27,
        leading=32,
        textColor=NAVY,
        alignment=TA_LEFT,
        spaceAfter=8,
    )
    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        fontName="Helvetica",
        fontSize=13,
        leading=18,
        textColor=BLUE,
        alignment=TA_LEFT,
    )
    cover_meta = ParagraphStyle(
        "CoverMeta",
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=MUTED,
        alignment=TA_LEFT,
    )
    story.extend(
        [
            Paragraph("Product and Administration Guide", title_style),
            Paragraph("Features, architecture, deployment, operations, regression, and evidence", subtitle_style),
            Spacer(1, 27 * mm),
            Paragraph("Version 2.6.0", cover_meta),
            Paragraph("Final public MIT engineering baseline", cover_meta),
            Spacer(1, 8 * mm),
            Paragraph("Contributor", cover_meta),
            Paragraph("<b>Sudheer Kumar Vatrapu</b>", cover_meta),
            NextPageTemplate("Body"),
            PageBreak(),
            make_heading("Contents", 1, style_map),
        ]
    )
    toc = TableOfContents()
    toc.levelStyles = [
        style_map["toc"],
        ParagraphStyle("TOC2", parent=style_map["toc"], leftIndent=24, fontSize=8.3, textColor=BLUE),
        ParagraphStyle("TOC3", parent=style_map["toc"], leftIndent=36, fontSize=7.8, textColor=MUTED),
    ]
    story.append(toc)

    source = source_path.read_text(encoding="utf-8")
    start = source.find("# Document Control")
    if start < 0:
        raise ValueError("PRODUCT_GUIDE.md must contain '# Document Control'")
    story.extend(parse_markdown(source[start:], style_map, frame_width))
    doc.multiBuild(story)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build(args.source, args.output)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
