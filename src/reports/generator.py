import os
import yaml
from datetime import datetime

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

OUTPUT_DIR = config["report"]["output_dir"]
CHARTS_DIR = config["report"]["charts_dir"]


def generate_pdf_report(
    session_summary: dict,
    ai_summary: str,
    posture_history: list,
    emotion_counts: dict
) -> str:
    """
    Build a PDF wellness report.
    Returns the path to the saved PDF file.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Image,
        Table, TableStyle, HRFlowable
    )
    from src.reports.charts import posture_timeline_chart, emotion_pie_chart, blink_rate_chart

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(CHARTS_DIR, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = os.path.join(OUTPUT_DIR, f"wellness_report_{ts}.pdf")

    # Generate charts
    posture_chart = posture_timeline_chart(
        posture_history,
        os.path.join(CHARTS_DIR, f"posture_{ts}.png")
    )
    emotion_chart = emotion_pie_chart(
        emotion_counts,
        os.path.join(CHARTS_DIR, f"emotion_{ts}.png")
    )
    blink_chart = blink_rate_chart(
        blink_rate=float(session_summary.get("blink_rate", 0)),
        baseline=float(session_summary.get("baseline_blink", config["user"]["baseline_blink"])),
        threshold=float(config["alerts"]["blink_rate_low"]),
        output_path=os.path.join(CHARTS_DIR, f"blink_{ts}.png")
    )

    doc = SimpleDocTemplate(
        pdf_path, pagesize=letter,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "WTitle", parent=styles["Title"],
        fontSize=20, textColor=colors.HexColor("#2c3e50"), spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        "WSubtitle", parent=styles["Normal"],
        fontSize=11, textColor=colors.HexColor("#7f8c8d"), spaceAfter=12
    )
    section_style = ParagraphStyle(
        "WSection", parent=styles["Heading2"],
        fontSize=13, textColor=colors.HexColor("#2c3e50"), spaceBefore=14, spaceAfter=6
    )
    body_style = ParagraphStyle(
        "WBody", parent=styles["Normal"],
        fontSize=10, leading=16, textColor=colors.HexColor("#2c3e50")
    )

    story = []

    # Header
    story.append(Paragraph("Wellness Session Report", title_style))
    story.append(Paragraph(
        f"{session_summary.get('user_name', 'User')} — "
        f"{datetime.now().strftime('%B %d, %Y at %H:%M')}",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#ecf0f1")))
    story.append(Spacer(1, 0.2 * inch))

    # Metrics table
    story.append(Paragraph("Session Summary", section_style))
    metrics_data = [
        ["Metric", "Value"],
        ["Duration", f"{session_summary.get('seated_mins', 0):.1f} mins"],
        ["Posture Score", f"{session_summary.get('posture_score', 0)}/100  (trend: {session_summary.get('posture_trend', 'stable')})"],
        ["Blink Rate", f"{session_summary.get('blink_rate', 0)}/min  (baseline: {session_summary.get('baseline_blink', 15)}/min)"],
        ["Dominant Emotion", f"{session_summary.get('dominant_emotion', 'neutral')}  ({session_summary.get('emotion_pct', 0)}% of session)"],
        ["Voice Stress Index", f"{session_summary.get('stress_index', 0.0):.2f} / 1.0"],
        ["Alerts Triggered", str(session_summary.get("alerts_triggered", 0))],
    ]
    table = Table(metrics_data, colWidths=[2.4 * inch, 4.1 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
        ("PADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.25 * inch))

    # Posture timeline
    if posture_chart and os.path.exists(posture_chart):
        story.append(Paragraph("Posture Timeline", section_style))
        story.append(Image(posture_chart, width=6.5 * inch, height=2.6 * inch))
        story.append(Spacer(1, 0.15 * inch))

    # Blink rate chart
    if blink_chart and os.path.exists(blink_chart):
        story.append(Paragraph("Blink Rate Analysis", section_style))
        story.append(Image(blink_chart, width=4 * inch, height=2.8 * inch))
        story.append(Spacer(1, 0.15 * inch))

    # Emotion pie
    if emotion_chart and os.path.exists(emotion_chart):
        story.append(Paragraph("Emotion Distribution", section_style))
        story.append(Image(emotion_chart, width=3.5 * inch, height=3.5 * inch))
        story.append(Spacer(1, 0.15 * inch))

    # AI summary
    if ai_summary:
        story.append(Paragraph("AI Wellness Analysis", section_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#ecf0f1")))
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph(ai_summary.replace("\n", "<br/>"), body_style))

    doc.build(story)
    return pdf_path
