from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from html import escape
from pathlib import Path, PurePosixPath
from typing import Any

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph

PAGE_W, PAGE_H = A4
MARGIN = 42
CONTENT_W = PAGE_W - 2 * MARGIN

INK = "#17182B"
PAPER = "#FFFDF8"
MUTED = "#697086"
LINE = "#DEDDE4"
BLUE = "#3155F5"
VIOLET = "#8355D9"
ORANGE = "#E68A34"
CORAL = "#E25360"
LIME = "#B7D953"
TEAL = "#17877F"
PALE = "#F4F1EB"
SEVERITY_ORDER = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO")
SEVERITY_COLORS = {
    "CRITICAL": "#8B1734",
    "HIGH": CORAL,
    "MEDIUM": ORANGE,
    "LOW": TEAL,
    "INFO": BLUE,
}
SEVERITY_TINTS = {
    "CRITICAL": "#F7E4EA",
    "HIGH": "#FCE7E7",
    "MEDIUM": "#FAECDD",
    "LOW": "#E4F2EF",
    "INFO": "#E8ECFF",
}


def _font_names() -> tuple[str, str]:
    """Use a bundled Matplotlib font when available, with portable PDF core-font fallbacks."""
    try:
        from matplotlib import get_data_path

        font_dir = Path(get_data_path()) / "fonts" / "ttf"
        regular = font_dir / "DejaVuSans.ttf"
        bold = font_dir / "DejaVuSans-Bold.ttf"
        if regular.exists() and bold.exists():
            if "SentinalSans" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("SentinalSans", str(regular)))
                pdfmetrics.registerFont(TTFont("SentinalSans-Bold", str(bold)))
                pdfmetrics.registerFontFamily(
                    "SentinalSans",
                    normal="SentinalSans",
                    bold="SentinalSans-Bold",
                    italic="SentinalSans",
                    boldItalic="SentinalSans-Bold",
                )
            return "SentinalSans", "SentinalSans-Bold"
    except Exception:
        pass
    return "Helvetica", "Helvetica-Bold"


FONT, FONT_BOLD = _font_names()

TITLE_STYLE = ParagraphStyle(
    "ReportTitle", fontName=FONT_BOLD, fontSize=25, leading=29, textColor=HexColor(INK),
    alignment=TA_LEFT, wordWrap="CJK",
)
SUBTITLE_STYLE = ParagraphStyle(
    "ReportSubtitle", fontName=FONT, fontSize=9, leading=13, textColor=HexColor(MUTED),
    alignment=TA_LEFT, wordWrap="CJK",
)
BODY_STYLE = ParagraphStyle(
    "ReportBody", fontName=FONT, fontSize=8.1, leading=11.2, textColor=HexColor(INK),
    alignment=TA_LEFT, wordWrap="CJK",
)
SMALL_STYLE = ParagraphStyle(
    "ReportSmall", fontName=FONT, fontSize=7.2, leading=9.2, textColor=HexColor(MUTED),
    alignment=TA_LEFT, wordWrap="CJK",
)
TINY_STYLE = ParagraphStyle(
    "ReportTiny", fontName=FONT, fontSize=6.5, leading=8, textColor=HexColor(MUTED),
    alignment=TA_LEFT, wordWrap="CJK",
)


def _short(value: Any, limit: int) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: max(1, limit - 3)].rstrip() + "..."


def _display_time(value: Any) -> str:
    if not value:
        return "Not recorded"
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    except (TypeError, ValueError):
        return _short(value, 72)


def _draw_paragraph(
    canvas: Canvas,
    text: str,
    x: float,
    top: float,
    width: float,
    style: ParagraphStyle = BODY_STYLE,
    *,
    markup: bool = False,
) -> float:
    paragraph = Paragraph(text if markup else escape(str(text)), style)
    _, height = paragraph.wrap(max(1, width), max(1, top))
    paragraph.drawOn(canvas, x, top - height)
    return top - height


def _draw_label(canvas: Canvas, text: str, x: float, y: float, color: str = MUTED, size: float = 7) -> None:
    canvas.setFillColor(HexColor(color))
    canvas.setFont(FONT_BOLD, size)
    canvas.drawString(x, y, text.upper())


def _draw_chrome(canvas: Canvas, page_no: int, analysis_id: str) -> None:
    canvas.setFillColor(HexColor(PAPER))
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.setFillColor(HexColor(INK))
    canvas.roundRect(MARGIN, PAGE_H - 38, 23, 23, 5, fill=1, stroke=0)
    canvas.setFillColor(HexColor(PAPER))
    canvas.setFont(FONT_BOLD, 10)
    canvas.drawCentredString(MARGIN + 11.5, PAGE_H - 30, "S")
    canvas.setFillColor(HexColor(INK))
    canvas.setFont(FONT_BOLD, 9)
    canvas.drawString(MARGIN + 31, PAGE_H - 25, "SENTINAL")
    canvas.setFillColor(HexColor(MUTED))
    canvas.setFont(FONT, 6.7)
    canvas.drawString(MARGIN + 31, PAGE_H - 35, "CODEBASE INTELLIGENCE")
    canvas.setFont(FONT_BOLD, 6.8)
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 29, "EVIDENCE FIRST / STATIC ANALYSIS")
    canvas.setStrokeColor(HexColor(LINE))
    canvas.setLineWidth(0.7)
    canvas.line(MARGIN, PAGE_H - 47, PAGE_W - MARGIN, PAGE_H - 47)
    canvas.line(MARGIN, 34, PAGE_W - MARGIN, 34)
    canvas.setFillColor(HexColor(MUTED))
    canvas.setFont(FONT, 6.4)
    if analysis_id:
        canvas.drawString(MARGIN, 21, f"ANALYSIS { _short(analysis_id, 44) }")
    else:
        canvas.drawString(MARGIN, 21, "UNDERSTAND YOUR CODE. PROVE EVERY DECISION.")
    canvas.setFont(FONT_BOLD, 7)
    canvas.drawRightString(PAGE_W - MARGIN, 21, f"{page_no:02d} / 04")


def _page_heading(canvas: Canvas, eyebrow: str, title: str, subtitle: str = "") -> float:
    _draw_label(canvas, eyebrow, MARGIN, PAGE_H - 68, BLUE, 7.2)
    bottom = _draw_paragraph(canvas, _short(title, 110), MARGIN, PAGE_H - 77, CONTENT_W, TITLE_STYLE)
    if subtitle:
        bottom = _draw_paragraph(canvas, _short(subtitle, 250), MARGIN, bottom - 5, CONTENT_W, SUBTITLE_STYLE)
    return bottom


def _severity_counts(findings: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(str(f.get("severity", "INFO")).upper() for f in findings)
    return {severity: int(counts.get(severity, 0)) for severity in SEVERITY_ORDER}


def _severity_rank(finding: dict[str, Any]) -> tuple[int, float, str, int]:
    severity = str(finding.get("severity", "INFO")).upper()
    try:
        confidence = float(finding.get("confidence", 0) or 0)
    except (TypeError, ValueError):
        confidence = 0
    return (
        SEVERITY_ORDER.index(severity) if severity in SEVERITY_ORDER else len(SEVERITY_ORDER),
        -confidence,
        str(finding.get("path", "")),
        int(finding.get("line_start", 0) or 0),
    )


def _triage_counts(findings: list[dict[str, Any]]) -> Counter[str]:
    counts = Counter()
    for finding in findings:
        status = str(finding.get("status") or "open").lower()
        counts[status] += 1
    return counts


def _summary_values(analysis: dict[str, Any]) -> dict[str, Any]:
    summary = analysis.get("summary") or {}
    findings = list(analysis.get("findings") or [])
    file_rows = list(analysis.get("files") or [])
    statuses = _triage_counts(findings)
    try:
        health = int(summary["health_score"]) if summary.get("health_score") is not None else None
    except (TypeError, ValueError):
        health = None
    return {
        "files": int(summary.get("files_analyzed", len(file_rows)) or 0),
        "source_lines": int(summary.get("source_lines", 0) or 0),
        "findings": findings,
        "severity": _severity_counts(findings),
        "health": health,
        "statuses": statuses,
    }


def _draw_metadata_grid(
    canvas: Canvas,
    source: dict[str, Any],
    metadata: dict[str, Any],
    generated_at: str,
    top: float,
) -> float:
    source_type = str(source.get("type") or "source").lower()
    source_label = {"github": "GitHub repository", "upload": "ZIP upload", "demo": "Demo fixture"}.get(source_type, source_type.title())
    source_location = source.get("repository_url") or source.get("filename") or source.get("repo_name") or "Not recorded"
    fields = [
        ("Input", f"{source_label} / {_short(source_location, 92)}"),
        ("Branch", source.get("branch") or "Not available"),
        ("Revision", source.get("commit_sha") or "Not available"),
        ("Analysis ID", metadata.get("analysis_id") or "Not recorded"),
        ("Scan snapshot (UTC)", _display_time(source.get("snapshot_at"))),
        ("Submitted (UTC)", _display_time(metadata.get("submitted_at"))),
        ("Analysis completed (UTC)", _display_time(metadata.get("analysis_completed_at"))),
        ("Report generated (UTC)", _display_time(generated_at)),
    ]
    cols, rows, gap = 2, 4, 7
    cell_w = (CONTENT_W - gap) / cols
    cell_h = 37
    y_top = top
    for index, (label, value) in enumerate(fields):
        row, col = divmod(index, cols)
        x = MARGIN + col * (cell_w + gap)
        y = y_top - (row + 1) * cell_h - row * 5
        canvas.setFillColor(HexColor("#FFFFFF" if index % 2 == 0 else "#F8F5EF"))
        canvas.setStrokeColor(HexColor(LINE))
        canvas.setLineWidth(0.65)
        canvas.roundRect(x, y, cell_w, cell_h, 7, fill=1, stroke=1)
        _draw_label(canvas, label, x + 10, y + cell_h - 12, MUTED, 6.1)
        value_style = ParagraphStyle(
            f"Meta{index}", fontName=FONT_BOLD, fontSize=7.2, leading=9,
            textColor=HexColor(INK), wordWrap="CJK",
        )
        _draw_paragraph(canvas, value, x + 10, y + cell_h - 17, cell_w - 20, value_style)
    return y_top - rows * cell_h - (rows - 1) * 5


def _tree_rows(files: list[dict[str, Any]], findings: list[dict[str, Any]], max_nodes: int = 11) -> tuple[list[tuple[tuple[str, ...], bool]], set[str]]:
    path_severity: dict[str, int] = {}
    for finding in findings:
        path = str(finding.get("path") or "")
        if not path:
            continue
        rank = _severity_rank(finding)[0]
        path_severity[path] = min(rank, path_severity.get(path, rank))
    candidates = sorted(
        files,
        key=lambda row: (
            path_severity.get(str(row.get("path", "")), len(SEVERITY_ORDER)),
            -int(row.get("loc", 0) or 0),
            str(row.get("path", "")).lower(),
        ),
    )
    nodes: set[tuple[str, ...]] = set()
    visible_files: set[str] = set()
    for row in candidates:
        path = str(row.get("path") or "").strip("/")
        parts = tuple(part for part in path.split("/") if part)
        if not parts:
            continue
        proposed = {parts[:i] for i in range(1, len(parts))} | {parts}
        if len(nodes | proposed) <= max_nodes:
            nodes.update(proposed)
            visible_files.add(path)
    ordered = sorted(nodes, key=lambda key: tuple(part.lower() for part in key))
    return [(node, len(node) > 0 and node in {tuple(Path(p).parts) for p in visible_files}) for node in ordered], visible_files


def _draw_tree(canvas: Canvas, x: float, top: float, width: float, height: float, analysis: dict[str, Any]) -> int:
    files = list(analysis.get("files") or [])
    findings = list(analysis.get("findings") or [])
    rows, visible_files = _tree_rows(files, findings)
    canvas.setFillColor(HexColor("#FFFFFF"))
    canvas.setStrokeColor(HexColor(LINE))
    canvas.roundRect(x, top - height, width, height, 10, fill=1, stroke=1)
    _draw_label(canvas, "REPOSITORY SHAPE", x + 13, top - 20, INK, 7)
    canvas.setFillColor(HexColor(MUTED))
    canvas.setFont(FONT, 6.4)
    canvas.drawRightString(x + width - 13, top - 20, f"{len(files):,} analyzed")
    canvas.setStrokeColor(HexColor(LINE))
    canvas.line(x + 12, top - 29, x + width - 12, top - 29)
    y = top - 47
    canvas.setFillColor(HexColor(VIOLET))
    canvas.circle(x + 21, y + 1, 3, fill=1, stroke=0)
    canvas.setFont(FONT_BOLD, 7.1)
    canvas.setFillColor(HexColor(INK))
    canvas.drawString(x + 32, y - 2, _short(str(analysis.get("project") or "repository root"), 33))
    y -= 17
    file_signal_paths = {str(f.get("path")) for f in findings if f.get("path")}
    line_h = 17
    available_rows = max(1, int((height - 96) / line_h))
    rows = rows[:available_rows]
    guide_x = x + 21
    if rows:
        canvas.setStrokeColor(HexColor("#D8D6DD"))
        canvas.setLineWidth(0.5)
        canvas.line(guide_x, y + 4, guide_x, y - (len(rows) - 1) * line_h - 3)
    for parts, is_file in rows:
        depth = max(0, len(parts) - 1)
        row_x = x + 31 + depth * 13
        base_y = y - 2
        canvas.setStrokeColor(HexColor("#D8D6DD"))
        canvas.line(guide_x, base_y + 2, row_x - 8, base_y + 2)
        path = "/".join(parts)
        if is_file and path in file_signal_paths:
            severity = min((f for f in findings if str(f.get("path")) == path), key=_severity_rank).get("severity", "INFO")
            marker = SEVERITY_COLORS.get(str(severity).upper(), BLUE)
        else:
            marker = BLUE if not is_file else MUTED
        canvas.setFillColor(HexColor(marker))
        if is_file:
            canvas.roundRect(row_x - 3, base_y - 2, 6, 7, 1.1, fill=1, stroke=0)
        else:
            canvas.roundRect(row_x - 5, base_y - 1, 10, 6, 1.2, fill=1, stroke=0)
        label = parts[-1] + ("/" if not is_file else "")
        canvas.setFillColor(HexColor(INK if is_file else MUTED))
        canvas.setFont(FONT if is_file else FONT_BOLD, 6.9)
        max_w = x + width - 12 - (row_x + 8)
        while label and pdfmetrics.stringWidth(label, FONT if is_file else FONT_BOLD, 6.9) > max_w:
            label = label[:-4].rstrip(" .") + "..."
        canvas.drawString(row_x + 8, base_y, label)
        y -= line_h
    visible_paths = {"/".join(parts) for parts, is_file in rows if is_file}
    omitted = max(0, len(files) - len(visible_paths))
    canvas.setFillColor(HexColor(MUTED))
    canvas.setFont(FONT, 6.2)
    canvas.drawString(x + 13, top - height + 13, f"{len(visible_paths)} shown / {omitted} additional file(s) omitted for readability")
    return len(visible_paths)


def _draw_metric_card(canvas: Canvas, x: float, y: float, width: float, height: float, label: str, value: str, note: str, accent: str) -> None:
    canvas.setFillColor(HexColor("#FFFFFF"))
    canvas.setStrokeColor(HexColor(LINE))
    canvas.roundRect(x, y, width, height, 9, fill=1, stroke=1)
    canvas.setFillColor(HexColor(accent))
    canvas.roundRect(x, y + 1, 4, height - 2, 2, fill=1, stroke=0)
    _draw_label(canvas, label, x + 12, y + height - 13, MUTED, 6.1)
    canvas.setFillColor(HexColor(INK))
    canvas.setFont(FONT_BOLD, 14)
    canvas.drawString(x + 12, y + 13, _short(value, 32))
    note_style = ParagraphStyle(
        f"Metric{label}", fontName=FONT, fontSize=6, leading=7.3,
        textColor=HexColor(MUTED), wordWrap="CJK",
    )
    _draw_paragraph(canvas, _short(note, 90), x + width * 0.47, y + height - 11, width * 0.48, note_style)


def _page1(canvas: Canvas, analysis: dict[str, Any], metadata: dict[str, Any], generated_at: str) -> None:
    values = _summary_values(analysis)
    project = _short(analysis.get("project") or "Codebase review", 100)
    _draw_label(canvas, "CODEBASE REVIEW / ENGINEERING REPORT", MARGIN, PAGE_H - 68, BLUE, 7.2)
    bottom = _draw_paragraph(canvas, project, MARGIN, PAGE_H - 77, CONTENT_W, TITLE_STYLE)
    _draw_paragraph(
        canvas,
        "Understand your code. Prove every decision. A measured snapshot of repository structure, findings, and next steps.",
        MARGIN, bottom - 4, CONTENT_W, SUBTITLE_STYLE,
    )
    metadata_bottom = _draw_metadata_grid(
        canvas, analysis.get("source") or {}, metadata, generated_at, PAGE_H - 137,
    )
    _draw_label(canvas, "PROJECT MAP / SUMMARY", MARGIN, metadata_bottom - 19, INK, 7.1)
    tree_top = metadata_bottom - 31
    panel_h = 327
    gap = 12
    tree_w = 268
    metric_x = MARGIN + tree_w + gap
    metric_w = CONTENT_W - tree_w - gap
    _draw_tree(canvas, MARGIN, tree_top, tree_w, panel_h, analysis)
    canvas.setFillColor(HexColor(PALE))
    canvas.setStrokeColor(HexColor(LINE))
    canvas.roundRect(metric_x, tree_top - panel_h, metric_w, panel_h, 10, fill=1, stroke=1)
    _draw_label(canvas, "ANALYSIS SUMMARY", metric_x + 13, tree_top - 20, INK, 7)
    canvas.setFillColor(HexColor(MUTED))
    canvas.setFont(FONT, 6.3)
    canvas.drawRightString(metric_x + metric_w - 13, tree_top - 20, "ONE SNAPSHOT")
    statuses = values["statuses"]
    open_count = statuses.get("open", 0) + statuses.get("investigate", 0)
    resolved_count = statuses.get("fixed", 0) + statuses.get("accepted", 0) + statuses.get("ignored", 0)
    critical_high = values["severity"]["CRITICAL"] + values["severity"]["HIGH"]
    metrics = [
        ("Files scanned", f"{values['files']:,}", "Files processed by enabled checks", BLUE),
        ("Source lines", f"{values['source_lines']:,}", "Non-comment, non-blank estimate", VIOLET),
        ("Findings", f"{len(values['findings']):,}", f"{critical_high:,} critical/high signals", CORAL),
        ("Health triage", f"{values['health']}/100" if values["health"] is not None else "Unavailable", "Heuristic indicator, not certification", ORANGE),
        ("Triage", f"{open_count:,} open", f"{resolved_count:,} fixed / accepted / ignored", TEAL),
    ]
    metric_h = 48
    metric_gap = 7
    y = tree_top - 42 - metric_h
    for label, value, note, accent in metrics:
        _draw_metric_card(canvas, metric_x + 12, y, metric_w - 24, metric_h, label, value, note, accent)
        y -= metric_h + metric_gap
    note_y = tree_top - panel_h - 16
    _draw_paragraph(
        canvas,
        "The hierarchy shows representative analyzed paths. A finding marks a review signal; paths without one are not certified safe. Submitted application code is not executed by default.",
        MARGIN, note_y, CONTENT_W, TINY_STYLE,
    )


def _draw_pie(canvas: Canvas, cx: float, cy: float, radius: float, inner_radius: float, counts: dict[str, int]) -> None:
    total = sum(counts.values())
    if total <= 0:
        canvas.setFillColor(HexColor("#ECE9E2"))
        canvas.circle(cx, cy, radius, fill=1, stroke=0)
    else:
        angle = 90
        for severity in SEVERITY_ORDER:
            count = counts.get(severity, 0)
            if count <= 0:
                continue
            extent = count / total * 360
            canvas.setFillColor(HexColor(SEVERITY_COLORS[severity]))
            canvas.wedge(cx - radius, cy - radius, cx + radius, cy + radius, angle, extent, fill=1, stroke=0)
            angle += extent
    canvas.setFillColor(HexColor(PAPER))
    canvas.circle(cx, cy, inner_radius, fill=1, stroke=0)
    canvas.setFillColor(HexColor(INK))
    canvas.setFont(FONT_BOLD, 18)
    canvas.drawCentredString(cx, cy + 3, f"{total:,}")
    canvas.setFillColor(HexColor(MUTED))
    canvas.setFont(FONT, 6.5)
    canvas.drawCentredString(cx, cy - 10, "FINDINGS")


def _draw_severity_legend(canvas: Canvas, x: float, top: float, counts: dict[str, int], total: int) -> None:
    y = top
    for severity in SEVERITY_ORDER:
        count = counts.get(severity, 0)
        canvas.setFillColor(HexColor(SEVERITY_COLORS[severity]))
        canvas.roundRect(x, y - 1, 9, 9, 2, fill=1, stroke=0)
        canvas.setFillColor(HexColor(INK))
        canvas.setFont(FONT_BOLD, 8)
        canvas.drawString(x + 17, y, severity.title())
        percent = f"{count / total:.0%}" if total else "-"
        canvas.setFillColor(HexColor(MUTED))
        canvas.setFont(FONT, 7)
        canvas.drawRightString(x + 231, y, f"{count:,}  /  {percent}")
        y -= 22


def _draw_bar_chart(canvas: Canvas, x: float, top: float, width: float, counts: dict[str, int]) -> None:
    max_count = max(counts.values(), default=0)
    label_w, bar_w, row_h = 63, width - 103, 29
    y = top
    for severity in SEVERITY_ORDER:
        count = counts.get(severity, 0)
        canvas.setFillColor(HexColor(INK))
        canvas.setFont(FONT_BOLD, 7.6)
        canvas.drawString(x, y - 2, severity.title())
        bar_x = x + label_w
        bar_y = y - 7
        canvas.setFillColor(HexColor("#ECE9E2"))
        canvas.roundRect(bar_x, bar_y, bar_w, 10, 4, fill=1, stroke=0)
        if count > 0 and max_count > 0:
            fill_w = max(4, bar_w * count / max_count)
            canvas.setFillColor(HexColor(SEVERITY_COLORS[severity]))
            canvas.roundRect(bar_x, bar_y, fill_w, 10, 4, fill=1, stroke=0)
        canvas.setFillColor(HexColor(INK))
        canvas.setFont(FONT_BOLD, 7.4)
        canvas.drawRightString(x + width, y - 2, f"{count:,}")
        y -= row_h


def _page2(canvas: Canvas, analysis: dict[str, Any]) -> None:
    values = _summary_values(analysis)
    bottom = _page_heading(
        canvas,
        "SIGNAL DISTRIBUTION / CHARTS",
        "What the enabled checks reported",
        "Both visualizations use the completed findings list and the same severity model shown in Sentinal.",
    )
    card_top = bottom - 16
    card_h = 260
    canvas.setFillColor(HexColor("#FFFFFF"))
    canvas.setStrokeColor(HexColor(LINE))
    canvas.roundRect(MARGIN, card_top - card_h, CONTENT_W, card_h, 10, fill=1, stroke=1)
    _draw_label(canvas, "FINDINGS DISTRIBUTION / PIE", MARGIN + 15, card_top - 22, INK, 7)
    total = len(values["findings"])
    canvas.setFillColor(HexColor(MUTED))
    canvas.setFont(FONT, 7)
    canvas.drawString(MARGIN + 15, card_top - 36, f"{total:,} reported finding(s), grouped by severity")
    _draw_pie(canvas, MARGIN + 126, card_top - 152, 78, 43, values["severity"])
    _draw_severity_legend(canvas, MARGIN + 254, card_top - 93, values["severity"], total)
    if total == 0:
        _draw_paragraph(
            canvas,
            "No findings were returned by the enabled checks. This empty result reflects scan scope and does not establish that the repository is issue-free.",
            MARGIN + 31, card_top - 231, CONTENT_W - 62, SMALL_STYLE,
        )
    else:
        _draw_paragraph(
            canvas,
            "Percentages use the complete findings count as their denominator. Counts are rule-based review signals, not confirmed vulnerabilities.",
            MARGIN + 254, card_top - 211, 228, SMALL_STYLE,
        )
    second_top = card_top - card_h - 14
    second_h = 278
    canvas.setFillColor(HexColor(PALE))
    canvas.setStrokeColor(HexColor(LINE))
    canvas.roundRect(MARGIN, second_top - second_h, CONTENT_W, second_h, 10, fill=1, stroke=1)
    _draw_label(canvas, "SEVERITY PROFILE / BAR GRAPH", MARGIN + 15, second_top - 22, INK, 7)
    canvas.setFillColor(HexColor(MUTED))
    canvas.setFont(FONT, 7)
    canvas.drawString(MARGIN + 15, second_top - 36, "Finding count by supported severity level")
    _draw_bar_chart(canvas, MARGIN + 18, second_top - 72, CONTENT_W - 42, values["severity"])
    score = values["health"]
    health_text = f"Health triage: {score}/100" if score is not None else "Health triage: unavailable"
    canvas.setFillColor(HexColor("#FFFFFF"))
    canvas.setStrokeColor(HexColor(LINE))
    canvas.roundRect(MARGIN + 15, second_top - second_h + 22, CONTENT_W - 30, 42, 7, fill=1, stroke=1)
    _draw_label(canvas, health_text, MARGIN + 27, second_top - second_h + 44, BLUE, 7)
    _draw_paragraph(
        canvas,
        "The health score is a confidence-weighted triage heuristic normalized by analyzed files. It is not a security rating or certification.",
        MARGIN + 27, second_top - second_h + 36, CONTENT_W - 54, TINY_STYLE,
    )


def _draw_severity_pill(canvas: Canvas, x: float, y: float, severity: str, status: str) -> None:
    severity = severity.upper()
    color = SEVERITY_COLORS.get(severity, BLUE)
    label = severity if severity in SEVERITY_ORDER else "OTHER"
    canvas.setFillColor(HexColor(SEVERITY_TINTS.get(severity, "#E8ECFF")))
    canvas.roundRect(x, y, 57, 16, 7, fill=1, stroke=0)
    canvas.setFillColor(HexColor(color))
    canvas.setFont(FONT_BOLD, 6.1)
    canvas.drawCentredString(x + 28.5, y + 5, label)
    canvas.setFillColor(HexColor(MUTED))
    canvas.setFont(FONT, 6)
    canvas.drawString(x + 64, y + 5, _short(status.upper(), 16))


def _draw_solution_card(canvas: Canvas, x: float, top: float, width: float, height: float, index: int, finding: dict[str, Any]) -> None:
    y = top - height
    canvas.setFillColor(HexColor("#FFFFFF"))
    canvas.setStrokeColor(HexColor(LINE))
    canvas.roundRect(x, y, width, height, 9, fill=1, stroke=1)
    canvas.setFillColor(HexColor(INK))
    canvas.roundRect(x + 12, top - 29, 24, 20, 5, fill=1, stroke=0)
    canvas.setFillColor(HexColor(PAPER))
    canvas.setFont(FONT_BOLD, 8)
    canvas.drawCentredString(x + 24, top - 22, f"{index:02d}")
    _draw_severity_pill(canvas, x + 45, top - 28, str(finding.get("severity", "INFO")), str(finding.get("status") or "open"))
    title_style = ParagraphStyle(
        f"SolutionTitle{index}", fontName=FONT_BOLD, fontSize=8.3, leading=10,
        textColor=HexColor(INK), wordWrap="CJK",
    )
    _draw_paragraph(canvas, _short(finding.get("title") or "Review finding", 105), x + 156, top - 10, width - 170, title_style)
    location = str(finding.get("path") or "Repository-level")
    if finding.get("line_start"):
        location += f":{finding.get('line_start')}"
    location_style = ParagraphStyle(
        f"SolutionLocation{index}", fontName=FONT, fontSize=6.1, leading=7.2,
        textColor=HexColor(MUTED), wordWrap="CJK",
    )
    _draw_paragraph(canvas, location, x + 45, top - 36, width - 58, location_style)
    divider_y = top - 47
    canvas.setStrokeColor(HexColor(LINE))
    canvas.line(x + 12, divider_y, x + width - 12, divider_y)
    description = _short(finding.get("description") or finding.get("impact") or "Review the rule evidence in context.", 150)
    remediation = _short(finding.get("remediation") or "Confirm the issue and document a suitable correction.", 170)
    verification = _short(finding.get("verification") or "Re-run the applicable checks after remediation.", 105)
    details_style = ParagraphStyle(
        f"SolutionDetails{index}", fontName=FONT, fontSize=6.5, leading=7.7,
        textColor=HexColor(INK), wordWrap="CJK",
    )
    _draw_paragraph(canvas, f"<b>Why:</b> {escape(description)}", x + 13, top - 52, width - 26, details_style, markup=True)
    _draw_paragraph(canvas, f"<b>Action:</b> {escape(remediation)}", x + 13, top - 67, width - 26, details_style, markup=True)
    _draw_paragraph(canvas, f"<b>Verify:</b> {escape(verification)}", x + 13, top - 83, width - 26, details_style, markup=True)


def _page3(canvas: Canvas, analysis: dict[str, Any]) -> None:
    values = _summary_values(analysis)
    findings = sorted(values["findings"], key=_severity_rank)
    _page_heading(
        canvas,
        "REMEDIATION / ACTIONABLE SOLUTIONS",
        "The remediation playbook",
        "Prioritized from the findings in this snapshot. Suggested changes are not represented as applied or verified.",
    )
    total = len(findings)
    high = values["severity"]["CRITICAL"] + values["severity"]["HIGH"]
    summary_top = PAGE_H - 151
    summary_h = 43
    summary = [
        ("PRIORITY SIGNALS", f"{high:,}", "Critical + high", CORAL),
        ("FINDINGS", f"{total:,}", "In this report snapshot", BLUE),
        ("ACTIONS SHOWN", f"{min(5, total):,}", f"{max(0, total - 5):,} additional in full queue", VIOLET),
    ]
    card_w = (CONTENT_W - 14) / 3
    for index, (label, value, note, color) in enumerate(summary):
        x = MARGIN + index * (card_w + 7)
        y = summary_top - summary_h
        canvas.setFillColor(HexColor("#FFFFFF"))
        canvas.setStrokeColor(HexColor(LINE))
        canvas.roundRect(x, y, card_w, summary_h, 8, fill=1, stroke=1)
        _draw_label(canvas, label, x + 11, y + 29, color, 6.2)
        canvas.setFillColor(HexColor(INK))
        canvas.setFont(FONT_BOLD, 13)
        canvas.drawString(x + 11, y + 9, value)
        canvas.setFillColor(HexColor(MUTED))
        canvas.setFont(FONT, 5.8)
        canvas.drawRightString(x + card_w - 10, y + 11, _short(note, 42))
    if not findings:
        y = 205
        h = 275
        canvas.setFillColor(HexColor("#FFFFFF"))
        canvas.setStrokeColor(HexColor(LINE))
        canvas.roundRect(MARGIN, y, CONTENT_W, h, 12, fill=1, stroke=1)
        _draw_label(canvas, "NO FINDINGS RETURNED", MARGIN + 24, y + h - 31, TEAL, 7)
        _draw_paragraph(
            canvas,
            "The enabled checks returned no findings for this snapshot. Keep the source scope and coverage notes in view; an empty result is not proof that the code is defect-free.",
            MARGIN + 24, y + h - 50, CONTENT_W - 48, BODY_STYLE,
        )
        _draw_paragraph(
            canvas,
            "Next steps: review the enabled security, quality, and architecture checks; run the project's own tests and security tools; then rescan the same revision to establish a comparable baseline.",
            MARGIN + 24, y + h - 117, CONTENT_W - 48, BODY_STYLE,
        )
        return
    shown = findings[:5]
    card_h = 99
    card_gap = 7
    top = summary_top - summary_h - 13
    for index, finding in enumerate(shown, start=1):
        _draw_solution_card(canvas, MARGIN, top, CONTENT_W, card_h, index, finding)
        top -= card_h + card_gap
    omitted = total - len(shown)
    if omitted:
        canvas.setFillColor(HexColor(MUTED))
        canvas.setFont(FONT, 6.8)
        canvas.drawString(MARGIN + 2, top - 2, f"{omitted:,} additional finding(s) remain in the full Findings queue.")


def _directory_risk_rows(findings: list[dict[str, Any]], limit: int = 6) -> list[tuple[str, dict[str, int]]]:
    buckets: dict[str, Counter[str]] = defaultdict(Counter)
    for finding in findings:
        path = str(finding.get("path") or "")
        directory = PurePosixPath(path).parent.as_posix() if path else "Repository-level"
        if directory in {"", "."}:
            directory = "Repository root"
        severity = str(finding.get("severity", "INFO")).upper()
        buckets[directory][severity] += 1
    ordered = sorted(
        buckets.items(),
        key=lambda item: (
            min((SEVERITY_ORDER.index(s) for s, count in item[1].items() if s in SEVERITY_ORDER and count), default=9),
            -sum(item[1].values()),
            item[0].lower(),
        ),
    )
    rows = [(name, {severity: int(counts.get(severity, 0)) for severity in SEVERITY_ORDER}) for name, counts in ordered[:limit]]
    if len(ordered) > limit:
        other: Counter[str] = Counter()
        for _, counts in ordered[limit:]:
            other.update(counts)
        rows.append(("Other paths", {severity: int(other.get(severity, 0)) for severity in SEVERITY_ORDER}))
    return rows


def _cell_tint(severity: str, count: int) -> str:
    if count <= 0:
        return "#F3F1EC"
    return SEVERITY_TINTS[severity]


def _draw_risk_map(canvas: Canvas, x: float, top: float, width: float, findings: list[dict[str, Any]]) -> None:
    _draw_label(canvas, "RISK CONCENTRATION MAP", x + 14, top - 20, INK, 7)
    _draw_paragraph(
        canvas,
        "Reported finding counts grouped by immediate parent directory. This is signal density, not exploitability or architectural coupling.",
        x + 14, top - 29, width - 28, TINY_STYLE,
    )
    rows = _directory_risk_rows(findings)
    if not rows:
        _draw_paragraph(
            canvas,
            "No directory-level map is available because the enabled checks returned no findings.",
            x + 14, top - 77, width - 28, BODY_STYLE,
        )
        return
    table_x = x + 14
    table_top = top - 62
    dir_w, sev_w, total_w = 167, 47, 48
    row_h = min(22, 125 / (len(rows) + 1))
    headers = [("DIRECTORY", dir_w)] + [(s[:1], sev_w) for s in SEVERITY_ORDER] + [("TOTAL", total_w)]
    cursor = table_x
    header_y = table_top - row_h
    for label, cell_w in headers:
        canvas.setFillColor(HexColor(INK))
        canvas.rect(cursor, header_y, cell_w, row_h, fill=1, stroke=0)
        canvas.setFillColor(HexColor(PAPER))
        canvas.setFont(FONT_BOLD, 6.2)
        if cell_w == dir_w:
            canvas.drawString(cursor + 6, header_y + row_h / 2 - 2, label)
        else:
            canvas.drawCentredString(cursor + cell_w / 2, header_y + row_h / 2 - 2, label)
        cursor += cell_w
    for row_index, (directory, counts) in enumerate(rows):
        row_y = table_top - row_h * (row_index + 2)
        canvas.setFillColor(HexColor("#FFFFFF" if row_index % 2 == 0 else "#F8F5EF"))
        canvas.rect(table_x, row_y, dir_w, row_h, fill=1, stroke=0)
        canvas.setFillColor(HexColor(INK))
        canvas.setFont(FONT, 6.2)
        label = _short(directory, 34)
        canvas.drawString(table_x + 6, row_y + row_h / 2 - 2, label)
        cursor = table_x + dir_w
        for severity in SEVERITY_ORDER:
            count = counts.get(severity, 0)
            canvas.setFillColor(HexColor(_cell_tint(severity, count)))
            canvas.rect(cursor, row_y, sev_w, row_h, fill=1, stroke=0)
            canvas.setFillColor(HexColor(SEVERITY_COLORS[severity] if count else MUTED))
            canvas.setFont(FONT_BOLD if count else FONT, 6.4)
            canvas.drawCentredString(cursor + sev_w / 2, row_y + row_h / 2 - 2, str(count))
            cursor += sev_w
        total = sum(counts.values())
        canvas.setFillColor(HexColor("#EEEAFD"))
        canvas.rect(cursor, row_y, total_w, row_h, fill=1, stroke=0)
        canvas.setFillColor(HexColor(INK))
        canvas.setFont(FONT_BOLD, 6.5)
        canvas.drawCentredString(cursor + total_w / 2, row_y + row_h / 2 - 2, str(total))
    legend_y = table_top - row_h * (len(rows) + 2) - 9
    cursor = table_x
    for severity in SEVERITY_ORDER:
        canvas.setFillColor(HexColor(SEVERITY_COLORS[severity]))
        canvas.circle(cursor + 3, legend_y + 2, 3, fill=1, stroke=0)
        canvas.setFillColor(HexColor(MUTED))
        canvas.setFont(FONT, 5.8)
        canvas.drawString(cursor + 9, legend_y, severity.title())
        cursor += 76


def _page4(canvas: Canvas, analysis: dict[str, Any], ai_summary: dict[str, Any], generated_at: str) -> None:
    values = _summary_values(analysis)
    findings = sorted(values["findings"], key=_severity_rank)
    _page_heading(
        canvas,
        "SIGNATURE FEATURE / DECISION SUPPORT",
        "The engineering intelligence brief",
        "A compact decision aid that keeps measured facts, rule signals, and guidance distinct.",
    )
    map_top = PAGE_H - 145
    map_h = 227
    canvas.setFillColor(HexColor("#FFFFFF"))
    canvas.setStrokeColor(HexColor(LINE))
    canvas.roundRect(MARGIN, map_top - map_h, CONTENT_W, map_h, 10, fill=1, stroke=1)
    _draw_risk_map(canvas, MARGIN + 1, map_top - 1, CONTENT_W - 2, findings)

    row_y = 224
    row_h = 201
    gap = 10
    col_w = (CONTENT_W - gap) / 2
    left_x = MARGIN
    right_x = MARGIN + col_w + gap
    for x in (left_x, right_x):
        canvas.setFillColor(HexColor(PALE))
        canvas.setStrokeColor(HexColor(LINE))
        canvas.roundRect(x, row_y, col_w, row_h, 10, fill=1, stroke=1)
    _draw_label(canvas, "FIX-FIRST ACTION PLAN", left_x + 13, row_y + row_h - 20, INK, 6.8)
    if findings:
        actions = [
            ("01", f"Confirm the {str(findings[0].get('severity', 'highest')).lower()} signal", f"Review {_short(findings[0].get('path') or 'the repository', 55)}{':' + str(findings[0].get('line_start')) if findings[0].get('line_start') else ''} against surrounding code and deployment context."),
            ("02", "Apply a confirmed correction", _short(findings[0].get("remediation") or "Use the finding's remediation guidance after confirming it applies.", 118)),
            ("03", "Verify and rescan", _short(findings[0].get("verification") or "Run the applicable project checks, then rescan the same revision.", 118)),
        ]
    else:
        actions = [
            ("01", "Review the enabled coverage", "Confirm the security, quality, and architecture checks match the intended review scope."),
            ("02", "Run project-specific checks", "Use the repository's tests and security tools to cover behavior outside static patterns."),
            ("03", "Keep a comparable baseline", "Rescan the same revision after any changes; no issue-free status is implied."),
        ]
    action_y = row_y + row_h - 44
    for number, title, body in actions:
        canvas.setFillColor(HexColor(VIOLET if number == "01" else BLUE))
        canvas.roundRect(left_x + 13, action_y - 1, 21, 18, 5, fill=1, stroke=0)
        canvas.setFillColor(HexColor(PAPER))
        canvas.setFont(FONT_BOLD, 6.5)
        canvas.drawCentredString(left_x + 23.5, action_y + 5, number)
        title_style = ParagraphStyle(
            f"ActionTitle{number}", fontName=FONT_BOLD, fontSize=7.2, leading=8.5,
            textColor=HexColor(INK), wordWrap="CJK",
        )
        _draw_paragraph(canvas, title, left_x + 42, action_y + 15, col_w - 55, title_style)
        _draw_paragraph(canvas, body, left_x + 42, action_y + 3, col_w - 55, TINY_STYLE)
        action_y -= 49

    _draw_label(canvas, "EVIDENCE / CONFIDENCE", right_x + 13, row_y + row_h - 20, INK, 6.8)
    confidence_values = []
    for finding in findings:
        try:
            if finding.get("confidence") is not None:
                confidence_values.append(float(finding["confidence"]))
        except (TypeError, ValueError):
            continue
    confidence_line = (
        f"Mean rule match confidence: {sum(confidence_values) / len(confidence_values):.0%} across {len(confidence_values)} finding(s). This is not a probability of exploitability."
        if confidence_values else "Rule match confidence was not provided for this snapshot."
    )
    summary = analysis.get("summary") or {}
    coverage = analysis.get("coverage") or {}
    limitations = []
    if coverage.get("runtime_execution"):
        limitations.append(str(coverage["runtime_execution"]))
    if coverage.get("dependency_advisory_database"):
        limitations.append(str(coverage["dependency_advisory_database"]))
    coverage_text = _short("; ".join(limitations) or "Coverage limitations were not supplied.", 180)
    narrative_mode = str(ai_summary.get("mode") or "No model-generated narrative") if isinstance(ai_summary, dict) else "No model-generated narrative"
    evidence_items = [
        f"Measured: {values['files']:,} files, {values['source_lines']:,} source lines, {len(findings):,} findings.",
        confidence_line,
        f"Narrative guidance: {_short(narrative_mode, 54)}.",
        f"Coverage: {coverage_text}",
    ]
    evidence_y = row_y + row_h - 43
    for index, item in enumerate(evidence_items):
        canvas.setFillColor(HexColor(TEAL if index == 0 else ORANGE if index == 1 else VIOLET if index == 2 else MUTED))
        canvas.circle(right_x + 17, evidence_y - 4, 2.5, fill=1, stroke=0)
        evidence_y = _draw_paragraph(canvas, item, right_x + 26, evidence_y + 5, col_w - 40, TINY_STYLE) - 11

    conclusion_y = 91
    conclusion_h = 120
    canvas.setFillColor(HexColor(INK))
    canvas.roundRect(MARGIN, conclusion_y, CONTENT_W, conclusion_h, 10, fill=1, stroke=0)
    _draw_label(canvas, "ENGINEERING CONCLUSION", MARGIN + 15, conclusion_y + conclusion_h - 21, LIME, 6.8)
    health = f"{values['health']}/100 heuristic health triage" if values["health"] is not None else "Health triage unavailable"
    severe_count = values["severity"]["CRITICAL"] + values["severity"]["HIGH"]
    if findings:
        first = findings[0]
        priority = _short(first.get("title") or "the highest-priority finding", 92)
        assessment = f"{health}. {severe_count:,} critical/high signal(s) were reported. Validate '{priority}' in context, apply a confirmed correction, then verify and rescan the same revision."
    else:
        assessment = f"{health}. The enabled checks returned no findings. Review coverage limits and run project-specific checks before treating this snapshot as a baseline."
    conclusion_style = ParagraphStyle(
        "Conclusion", fontName=FONT_BOLD, fontSize=9, leading=12,
        textColor=HexColor(PAPER), wordWrap="CJK",
    )
    _draw_paragraph(canvas, assessment, MARGIN + 15, conclusion_y + conclusion_h - 34, CONTENT_W - 30, conclusion_style)
    canvas.setFillColor(HexColor("#C9CDDC"))
    canvas.setFont(FONT, 6)
    canvas.drawString(MARGIN + 15, conclusion_y + 13, f"REPORT GENERATED { _display_time(generated_at) }  /  COVERAGE IS LIMITED TO THE ENABLED STATIC CHECKS")


def generate_pdf(
    analysis: dict[str, Any],
    ai_summary: dict[str, Any],
    output_path: Path,
    report_version: str = "3.0",
    metadata: dict[str, Any] | None = None,
) -> Path:
    """Create an explicitly composed, exactly four-page engineering report."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = metadata or {}
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    analysis_id = str(metadata.get("analysis_id") or "")
    document = Canvas(str(output_path), pagesize=A4, pageCompression=1)
    document.setTitle(f"Sentinal Codebase Review - {analysis.get('project', 'Codebase')}")
    document.setAuthor("Sentinal")
    document.setSubject("Evidence-based engineering intelligence and remediation brief")
    document.setCreator(f"Sentinal report renderer {report_version}")

    _draw_chrome(document, 1, analysis_id)
    _page1(document, analysis, metadata, generated_at)
    document.showPage()

    _draw_chrome(document, 2, analysis_id)
    _page2(document, analysis)
    document.showPage()

    _draw_chrome(document, 3, analysis_id)
    _page3(document, analysis)
    document.showPage()

    _draw_chrome(document, 4, analysis_id)
    _page4(document, analysis, ai_summary or {}, generated_at)
    document.showPage()
    document.save()
    return output_path
