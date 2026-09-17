from pathlib import Path
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from backend.schemas.mom import MinutesOfMeeting


LOCAL_TIMEZONE = ZoneInfo("Asia/Kolkata")


def format_local_datetime(value) -> str:
    """Convert a UTC-aware datetime to India Standard Time for display."""

    if value is None:
        return "Not available"

    if value.tzinfo is None:
        value = value.replace(tzinfo=ZoneInfo("UTC"))

    return value.astimezone(LOCAL_TIMEZONE).strftime(
        "%d %b %Y, %I:%M %p"
    )


class PDFExporter:
    """
    Export Minutes of Meeting into a PDF document.
    """

    def export(
        self,
        mom: MinutesOfMeeting,
        output_path: str | Path,
    ) -> Path:
        """
        Export a MinutesOfMeeting object to a PDF file.

        Args:
            mom: Structured Minutes of Meeting.
            output_path: Destination file path.

        Returns:
            Path: Path to the generated PDF file.
        """

        output_file = Path(output_path)

        output_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        document = SimpleDocTemplate(
            str(output_file),
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "MeetingTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontSize=22,
            leading=28,
            spaceAfter=18,
        )

        heading_style = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=14,
            leading=18,
            spaceBefore=12,
            spaceAfter=8,
        )

        body_style = ParagraphStyle(
            "BodyTextCustom",
            parent=styles["BodyText"],
            fontSize=10,
            leading=15,
            spaceAfter=6,
        )

        bullet_style = ParagraphStyle(
            "BulletText",
            parent=body_style,
            leftIndent=14,
            firstLineIndent=-8,
        )

        story = []

        # --------------------------------------------------
        # Title
        # --------------------------------------------------

        story.append(
            Paragraph(
                "MINUTES OF MEETING",
                title_style,
            )
        )

        # --------------------------------------------------
        # Meeting Information
        # --------------------------------------------------

        story.append(
            Paragraph(
                "Meeting Information",
                heading_style,
            )
        )

        story.append(
            Paragraph(
                f"<b>Meeting:</b> {mom.meeting_title}",
                body_style,
            )
        )

        if mom.meeting_date:
            date_text = format_local_datetime(
                mom.meeting_date
            )
        else:
            date_text = "Not available"

        story.append(
            Paragraph(
                f"<b>Date:</b> {date_text}",
                body_style,
            )
        )

        if mom.duration_seconds is not None:
            minutes = (
                mom.duration_seconds // 60
            )
            seconds = (
                mom.duration_seconds % 60
            )

            duration_text = (
                f"{minutes:02d}:{seconds:02d}"
            )
        else:
            duration_text = "Not available"

        story.append(
            Paragraph(
                f"<b>Duration:</b> {duration_text}",
                body_style,
            )
        )

        # --------------------------------------------------
        # Executive Summary
        # --------------------------------------------------

        story.append(
            Paragraph(
                "Executive Summary",
                heading_style,
            )
        )

        story.append(
            Paragraph(
                mom.summary,
                body_style,
            )
        )

        # --------------------------------------------------
        # Key Points
        # --------------------------------------------------

        story.append(
            Paragraph(
                "Key Points",
                heading_style,
            )
        )

        if mom.key_points:
            for point in mom.key_points:
                story.append(
                    Paragraph(
                        f"• {point}",
                        bullet_style,
                    )
                )
        else:
            story.append(
                Paragraph(
                    "No key points were recorded.",
                    body_style,
                )
            )

        # --------------------------------------------------
        # Decisions
        # --------------------------------------------------

        story.append(
            Paragraph(
                "Decisions",
                heading_style,
            )
        )

        if mom.decisions:
            for index, decision in enumerate(
                mom.decisions,
                start=1,
            ):
                story.append(
                    Paragraph(
                        f"{index}. {decision}",
                        body_style,
                    )
                )
        else:
            story.append(
                Paragraph(
                    "No decisions were recorded.",
                    body_style,
                )
            )

        # --------------------------------------------------
        # Action Items
        # --------------------------------------------------

        story.append(
            Paragraph(
                "Action Items",
                heading_style,
            )
        )

        if mom.action_items:
            table_data = [
                [
                    Paragraph("<b>Task</b>", body_style),
                    Paragraph("<b>Assignee</b>", body_style),
                    Paragraph("<b>Deadline</b>", body_style),
                    Paragraph("<b>Priority</b>", body_style),
                ]
            ]

            for item in mom.action_items:
                table_data.append(
                    [
                        Paragraph(
                            item.task,
                            body_style,
                        ),
                        Paragraph(
                            item.assignee or "Unassigned",
                            body_style,
                        ),
                        Paragraph(
                            item.deadline or "No deadline",
                            body_style,
                        ),
                        Paragraph(
                            item.priority,
                            body_style,
                        ),
                    ]
                )

            table = Table(
                table_data,
                colWidths=[
                    72 * mm,
                    32 * mm,
                    35 * mm,
                    25 * mm,
                ],
                repeatRows=1,
            )

            table.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            colors.HexColor("#E8EEF7"),
                        ),
                        (
                            "TEXTCOLOR",
                            (0, 0),
                            (-1, 0),
                            colors.black,
                        ),
                        (
                            "GRID",
                            (0, 0),
                            (-1, -1),
                            0.5,
                            colors.grey,
                        ),
                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "TOP",
                        ),
                        (
                            "LEFTPADDING",
                            (0, 0),
                            (-1, -1),
                            6,
                        ),
                        (
                            "RIGHTPADDING",
                            (0, 0),
                            (-1, -1),
                            6,
                        ),
                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            6,
                        ),
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            6,
                        ),
                    ]
                )
            )

            story.append(table)
        else:
            story.append(
                Paragraph(
                    "No action items were recorded.",
                    body_style,
                )
            )

        # --------------------------------------------------
        # Next Steps
        # --------------------------------------------------

        story.append(
            Paragraph(
                "Next Steps",
                heading_style,
            )
        )

        if mom.next_steps:
            for index, step in enumerate(
                mom.next_steps,
                start=1,
            ):
                story.append(
                    Paragraph(
                        f"{index}. {step}",
                        body_style,
                    )
                )
        else:
            story.append(
                Paragraph(
                    "No next steps were recorded.",
                    body_style,
                )
            )

        # --------------------------------------------------
        # Footer
        # --------------------------------------------------

        story.append(
            Spacer(
                1,
                15,
            )
        )

        story.append(
            Paragraph(
                "Generated by AI Meeting Intelligence",
                ParagraphStyle(
                    "Footer",
                    parent=body_style,
                    alignment=TA_CENTER,
                    fontSize=8,
                    textColor=colors.grey,
                ),
            )
        )

        # --------------------------------------------------
        # Generate PDF
        # --------------------------------------------------

        document.build(story)

        return output_file
