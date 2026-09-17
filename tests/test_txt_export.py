from backend.schemas.mom import (
    MinutesOfMeeting,
    MoMActionItem,
)
from exports.txt_exporter import TXTExporter


def main() -> None:
    """
    Test TXT export using a realistic Minutes of Meeting.
    """

    mom = MinutesOfMeeting(
        meeting_id=40,
        meeting_title="Streamlit Meeting",
        meeting_date="2026-09-15T22:04:32.419632Z",
        duration_seconds=41,
        summary=(
            "An important meeting is scheduled for Monday "
            "at 2 p.m., mandatory for the other team, "
            "and Thursday classes will be cancelled."
        ),
        key_points=[
            "Important meeting set for Monday at 2 p.m.",
            "Sabiq will organize the meeting.",
            "Attendance by the other team is required.",
            "Decision is final.",
            "No sessions or Class 4 will occur on Thursday.",
        ],
        decisions=[
            "Schedule and hold the meeting on Monday at 2 p.m.",
            "Cancel all sessions and Class 4 on Thursday.",
        ],
        action_items=[
            MoMActionItem(
                task="Organize and schedule the Monday meeting",
                assignee="Sabiq",
                deadline=None,
                priority="high",
            ),
            MoMActionItem(
                task="Ensure the other team attends the Monday meeting",
                assignee=None,
                deadline=None,
                priority="high",
            ),
        ],
        next_steps=[
            "Send reminder about the Monday 2 p.m. meeting.",
            "Update calendars with the Monday meeting details.",
            "Notify relevant parties of the Thursday session and Class 4 cancellation.",
        ],
    )

    exporter = TXTExporter()

    output_path = exporter.export(
        mom=mom,
        output_path="exports/meeting_40_mom.txt",
    )

    print(
        f"TXT export successful: {output_path}"
    )


if __name__ == "__main__":
    main()