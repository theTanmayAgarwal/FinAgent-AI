from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from finagent.schemas.domain import Recommendation


def render_pdf(ticker: str, report: Recommendation) -> bytes:
    out = BytesIO()
    doc = SimpleDocTemplate(out, pagesize=letter, title=f"FinAgent AI — {ticker}")
    styles = getSampleStyleSheet()
    story = [
        Paragraph(f"FinAgent AI Investment Committee: {ticker}", styles["Title"]),
        Spacer(1, 12),
    ]
    table = Table(
        [
            ["Recommendation", report.action],
            ["Score", f"{report.score:.1f}/100"],
            ["Confidence", f"{report.confidence:.0%}"],
            ["Illustrative allocation", f"{report.allocation_pct:.1f}%"],
        ],
        colWidths=[150, 300],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E8EEF8")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story += [
        table,
        Spacer(1, 14),
        Paragraph("Investment thesis", styles["Heading2"]),
        Paragraph(report.thesis, styles["BodyText"]),
        Paragraph("Bull case", styles["Heading2"]),
        Paragraph(report.bull_case, styles["BodyText"]),
        Paragraph("Bear case", styles["Heading2"]),
        Paragraph(report.bear_case, styles["BodyText"]),
        Paragraph("Agent evidence", styles["Heading2"]),
    ]
    for item in report.evidence:
        story += [
            Paragraph(
                f"<b>{item.agent.replace('_', ' ').title()}</b> — {item.summary} (score {item.score:.1f}, confidence {item.confidence:.0%})",
                styles["BodyText"],
            ),
            Spacer(1, 5),
        ]
    story += [Spacer(1, 16), Paragraph(report.disclaimer, styles["Italic"])]
    doc.build(story)
    return out.getvalue()
