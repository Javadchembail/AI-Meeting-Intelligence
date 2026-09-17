import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
import streamlit as st

from services.api_client import APIClient

from backend.schemas.mom import MinutesOfMeeting
from exports.docx_exporter import DOCXExporter
from exports.pdf_exporter import PDFExporter
from exports.txt_exporter import TXTExporter

from ui.components import (
    render_capability_cards,
    render_completed_banner,
    render_empty_state,
    render_footer,
    render_header,
    render_hero,
    render_insights_panel,
    render_meeting_metrics,
    render_recording_status,
    render_synced_audio_transcript,
    render_transcript_panel,
)

from ui.styles import load_custom_css


LOCAL_TIMEZONE = ZoneInfo("Asia/Kolkata")


def format_local_datetime(value: str | None) -> str:
    """
    Convert an ISO timestamp from UTC to India Standard Time
    before displaying it in the Streamlit UI.
    """

    if not value:
        return "Unknown date"

    try:
        parsed_datetime = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        if parsed_datetime.tzinfo is None:
            parsed_datetime = parsed_datetime.replace(
                tzinfo=ZoneInfo("UTC")
            )

        local_datetime = parsed_datetime.astimezone(
            LOCAL_TIMEZONE
        )

        return local_datetime.strftime(
            "%d %b %Y • %I:%M %p"
        )

    except (TypeError, ValueError):
        return str(value)


def initialize_dashboard_state() -> None:
    """Initialize Streamlit dashboard state."""

    defaults = {
        "meeting_active": False,
        "meeting_id": None,
        "meeting_title": None,
        "audio_path": None,
        "transcript": None,
        "word_timestamps": [],
        "recording_started_at": None,
        "completed_duration_seconds": 0,
        "start_in_progress": False,

        # Pause / Resume state
        "meeting_paused": False,
        "active_duration_before_pause": 0,
        "pause_started_at": None,

        # Live microphone level
        "audio_level": 0.0,

        # Speaker-aware transcript
        "speaker_transcript": None,

        # AI analysis
        "analysis": None,

        # Minutes of Meeting
        "mom": None,

        # Historical meeting viewer
        "selected_history_meeting_id": None,
    }

    for key, value in defaults.items():

        if key not in st.session_state:

            st.session_state[key] = value


def format_duration(
    total_seconds: int,
) -> str:
    """Convert seconds into HH:MM:SS format."""

    hours = total_seconds // 3600

    minutes = (
        total_seconds % 3600
    ) // 60

    seconds = (
        total_seconds % 60
    )

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{seconds:02d}"
    )


def get_current_active_duration() -> int:
    """
    Calculate active recording duration.

    Paused time is excluded.
    """

    accumulated = int(
        st.session_state.get(
            "active_duration_before_pause",
            0,
        )
    )

    if st.session_state.get(
        "meeting_paused",
        False,
    ):

        return accumulated

    started_at = st.session_state.get(
        "recording_started_at"
    )

    if started_at is None:

        return accumulated

    current_session_duration = max(
        0,
        int(
            time.time()
            - started_at
        ),
    )

    return (
        accumulated
        + current_session_duration
    )


def handle_start_meeting() -> bool:
    """Start the meeting immediately."""

    if st.session_state.get(
        "meeting_active",
        False,
    ):

        return False

    if st.session_state.get(
        "start_in_progress",
        False,
    ):

        return False

    st.session_state[
        "start_in_progress"
    ] = True

    try:

        client = APIClient()

        meeting = client.start_meeting(
            title="Streamlit Meeting"
        )

        st.session_state[
            "meeting_active"
        ] = True

        st.session_state[
            "meeting_id"
        ] = meeting["id"]

        st.session_state[
            "meeting_title"
        ] = meeting["title"]

        st.session_state[
            "audio_path"
        ] = None

        st.session_state[
            "transcript"
        ] = None

        st.session_state[
            "word_timestamps"
        ] = []

        st.session_state[
            "speaker_transcript"
        ] = None

        st.session_state[
            "completed_duration_seconds"
        ] = 0

        # Reset pause/resume state.
        st.session_state[
            "meeting_paused"
        ] = False

        st.session_state[
            "active_duration_before_pause"
        ] = 0

        st.session_state[
            "pause_started_at"
        ] = None

        # Reset live microphone level.
        st.session_state[
            "audio_level"
        ] = 0.0

        # Reset previous AI analysis.
        st.session_state[
            "analysis"
        ] = None

        # Reset previous Minutes of Meeting.
        st.session_state[
            "mom"
        ] = None

        started_at = meeting.get(
            "started_at"
        )

        if started_at:

            parsed_started_at = (
                datetime.fromisoformat(
                    started_at.replace(
                        "Z",
                        "+00:00",
                    )
                )
            )

            st.session_state[
                "recording_started_at"
            ] = (
                parsed_started_at.timestamp()
            )

        else:

            st.session_state[
                "recording_started_at"
            ] = time.time()

        st.session_state[
            "start_in_progress"
        ] = False

        return True

    except Exception as exc:

        st.session_state[
            "start_in_progress"
        ] = False

        st.session_state[
            "meeting_active"
        ] = False

        st.session_state[
            "meeting_id"
        ] = None

        st.session_state[
            "recording_started_at"
        ] = None

        st.session_state[
            "audio_level"
        ] = 0.0

        st.error(
            f"Unable to start meeting: {exc}"
        )

        return False


def handle_pause_meeting() -> bool:
    """Pause the active meeting recording."""

    meeting_id = st.session_state.get(
        "meeting_id"
    )

    if meeting_id is None:

        st.error(
            "No active meeting was found."
        )

        return False

    if st.session_state.get(
        "meeting_paused",
        False,
    ):

        return False

    try:

        # Calculate the duration BEFORE changing
        # the Streamlit state to paused.
        current_duration = (
            get_current_active_duration()
        )

        client = APIClient()

        client.pause_meeting(
            meeting_id
        )

        st.session_state[
            "active_duration_before_pause"
        ] = current_duration

        st.session_state[
            "meeting_paused"
        ] = True

        st.session_state[
            "pause_started_at"
        ] = time.time()

        st.session_state[
            "recording_started_at"
        ] = None

        # Silence the waveform while paused.
        st.session_state[
            "audio_level"
        ] = 0.0

        return True

    except Exception as exc:

        st.error(
            f"Unable to pause meeting: {exc}"
        )

        return False


def handle_resume_meeting() -> bool:
    """Resume the paused meeting recording."""

    meeting_id = st.session_state.get(
        "meeting_id"
    )

    if meeting_id is None:

        st.error(
            "No active meeting was found."
        )

        return False

    if not st.session_state.get(
        "meeting_paused",
        False,
    ):

        return False

    try:

        client = APIClient()

        client.resume_meeting(
            meeting_id
        )

        # Start a new active-duration period.
        st.session_state[
            "recording_started_at"
        ] = time.time()

        st.session_state[
            "meeting_paused"
        ] = False

        st.session_state[
            "pause_started_at"
        ] = None

        st.session_state[
            "audio_level"
        ] = 0.0

        return True

    except Exception as exc:

        st.error(
            f"Unable to resume meeting: {exc}"
        )

        return False


def format_transcript_timestamp(seconds: float) -> str:
    """Format transcript time in MM:SS or HH:MM:SS format."""

    total_seconds = max(0, int(seconds))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    remaining_seconds = total_seconds % 60

    if hours > 0:
        return (
            f"{hours:02d}:{minutes:02d}:"
            f"{remaining_seconds:02d}"
        )

    return f"{minutes:02d}:{remaining_seconds:02d}"


def render_speaker_transcript(
    speaker_transcript: dict | None,
) -> None:
    """Render the persisted speaker-aware meeting transcript."""

    if not speaker_transcript:
        return

    segments = speaker_transcript.get("segments") or []
    speakers = speaker_transcript.get("speakers") or []

    st.markdown("### 🗣️ Speaker Transcript")

    if not segments:
        st.caption("No speaker transcript segments are available.")
        return

    speaker_count = len(speakers)
    turn_label = "turn" if len(segments) == 1 else "turns"
    speaker_label = "speaker" if speaker_count == 1 else "speakers"

    st.caption(
        f"{speaker_count} {speaker_label} • "
        f"{len(segments)} speaker {turn_label}"
    )

    for index, segment in enumerate(segments):
        speaker = segment.get("speaker", "UNKNOWN")
        start = float(segment.get("start", 0.0) or 0.0)
        end = float(segment.get("end", start) or start)
        text = str(segment.get("text", "") or "").strip()

        if not text:
            continue

        st.markdown(
            f"**{speaker}**  "
            f"`{format_transcript_timestamp(start)} → "
            f"{format_transcript_timestamp(end)}`"
        )
        st.write(text)

        if index < len(segments) - 1:
            st.divider()


@st.fragment(
    run_every="1s"
)
def render_live_recording() -> None:
    """
    Render the active recording interface.

    The microphone audio level is fetched from
    FastAPI every second and passed to the live
    waveform renderer.
    """

    elapsed_seconds = (
        get_current_active_duration()
    )

    duration = format_duration(
        elapsed_seconds
    )

    meeting_id = st.session_state.get(
        "meeting_id"
    )

    # --------------------------------------------------
    # FETCH REAL MICROPHONE AUDIO LEVEL
    # --------------------------------------------------

    if (
        meeting_id is not None
        and not st.session_state.get(
            "meeting_paused",
            False,
        )
    ):

        try:

            client = APIClient()

            audio_level = (
                client.get_audio_level(
                    meeting_id
                )
            )

            st.session_state[
                "audio_level"
            ] = audio_level

        except Exception:

            # Do not interrupt the recording UI
            # if one level request fails.
            #
            # Keep the previous value instead.
            pass

    else:

        st.session_state[
            "audio_level"
        ] = 0.0

    audio_level = float(
        st.session_state.get(
            "audio_level",
            0.0,
        )
    )

    if st.session_state.get(
        "meeting_paused",
        False,
    ):

        st.html(
            """
            <div style="
                padding:0.8rem 1rem;
                margin-bottom:1rem;
                border-radius:14px;

                background:
                    linear-gradient(
                        135deg,
                        rgba(120,53,15,0.32),
                        rgba(15,23,42,0.82)
                    );

                border:
                    1px solid
                    rgba(251,191,36,0.22);

                text-align:center;
            ">

                <div style="
                    color:#fbbf24;
                    font-weight:800;
                    font-size:0.82rem;
                    letter-spacing:0.08em;
                    text-transform:uppercase;
                ">
                    ⏸️ Meeting Paused
                </div>

                <div style="
                    color:#94a3b8;
                    font-size:0.76rem;
                    margin-top:0.3rem;
                ">
                    Your recording is paused.
                    Resume when you're ready.
                </div>

            </div>
            """
        )

    else:

        render_recording_status(
            duration=duration,
            audio_level=audio_level,
        )

    render_meeting_metrics(
        duration=duration,
        words=0,
        participants=0,
    )

    st.divider()

    left_column, right_column = (
        st.columns(2)
    )

    with left_column:

        render_transcript_panel(
            transcript=""
        )

    with right_column:

        render_insights_panel()


def render_agentic_processing(
    container,
    active_step: int,
    completed_steps: set[int] | None = None,
) -> None:
    """Render the agentic AI processing workflow."""

    completed_steps = completed_steps or set()

    steps = [
        (1, "Capture Agent", "Securing your meeting recording", "🎙️"),
        (2, "Transcript Agent", "Understanding the conversation", "📝"),
        (3, "Intelligence Agent", "Extracting decisions and actions", "🧠"),
        (4, "MoM Agent", "Structuring the Minutes of Meeting", "📋"),
        (5, "Memory Agent", "Saving meeting intelligence", "💾"),
    ]

    cards = []

    for number, name, description, icon in steps:
        if number in completed_steps:
            state_class = "complete"
            marker = "✓"
            status = "Complete"
        elif number == active_step:
            state_class = "active"
            marker = "✦"
            status = "Working"
        else:
            state_class = "pending"
            marker = str(number)
            status = "Queued"

        cards.append(
            f"""
            <div class=\"agent-step {state_class}\">
                <div class=\"agent-marker\">{marker}</div>
                <div class=\"agent-icon\">{icon}</div>
                <div class=\"agent-copy\">
                    <div class=\"agent-name\">{name}</div>
                    <div class=\"agent-description\">{description}</div>
                </div>
                <div class=\"agent-status\">{status}</div>
            </div>
            """
        )

    current_name = steps[active_step - 1][1]

    container.html(
        f"""
        <style>
            .agent-shell {{
                margin: 1.2rem 0 1.5rem 0;
                padding: 1.5rem;
                border: 1px solid rgba(139, 92, 246, 0.28);
                border-radius: 24px;
                background:
                    radial-gradient(circle at 15% 10%, rgba(99,102,241,.18), transparent 35%),
                    radial-gradient(circle at 90% 90%, rgba(168,85,247,.15), transparent 35%),
                    linear-gradient(145deg, rgba(17,24,39,.96), rgba(10,10,25,.98));
                box-shadow: 0 20px 70px rgba(79,70,229,.12);
                font-family: inherit;
            }}

            .agent-header {{
                display:flex;
                align-items:center;
                gap:1rem;
                margin-bottom:1.25rem;
            }}

            .agent-orb {{
                width:54px;
                height:54px;
                border-radius:18px;
                display:flex;
                align-items:center;
                justify-content:center;
                font-size:1.45rem;
                background: linear-gradient(135deg, #6366f1, #a855f7, #ec4899);
                box-shadow: 0 0 0 6px rgba(139,92,246,.08), 0 0 35px rgba(139,92,246,.35);
                animation: agentPulse 1.8s ease-in-out infinite;
            }}

            .agent-title {{
                color:#f8fafc;
                font-size:1.08rem;
                font-weight:800;
                letter-spacing:-.01em;
            }}

            .agent-subtitle {{
                color:#94a3b8;
                font-size:.78rem;
                margin-top:.22rem;
            }}

            .agent-live {{
                margin-left:auto;
                padding:.34rem .65rem;
                border-radius:999px;
                background:rgba(99,102,241,.12);
                border:1px solid rgba(129,140,248,.22);
                color:#c4b5fd;
                font-size:.68rem;
                font-weight:800;
                text-transform:uppercase;
                letter-spacing:.09em;
            }}

            .agent-live::before {{
                content:"";
                display:inline-block;
                width:6px;
                height:6px;
                margin-right:6px;
                border-radius:50%;
                background:#a78bfa;
                box-shadow:0 0 10px #a78bfa;
                animation: dotPulse 1s infinite;
            }}

            .agent-steps {{
                display:grid;
                gap:.58rem;
            }}

            .agent-step {{
                display:flex;
                align-items:center;
                gap:.75rem;
                padding:.72rem .8rem;
                border-radius:15px;
                border:1px solid rgba(148,163,184,.08);
                background:rgba(15,23,42,.46);
                transition:all .25s ease;
            }}

            .agent-step.active {{
                border-color:rgba(129,140,248,.35);
                background:linear-gradient(90deg, rgba(79,70,229,.16), rgba(168,85,247,.07));
                box-shadow:inset 3px 0 0 #8b5cf6, 0 8px 25px rgba(79,70,229,.08);
            }}

            .agent-step.complete {{
                border-color:rgba(34,197,94,.14);
                background:rgba(22,101,52,.08);
            }}

            .agent-marker {{
                width:23px;
                height:23px;
                flex:0 0 23px;
                display:flex;
                align-items:center;
                justify-content:center;
                border-radius:50%;
                font-size:.67rem;
                font-weight:900;
                color:#94a3b8;
                background:rgba(148,163,184,.08);
            }}

            .active .agent-marker {{
                color:#ddd6fe;
                background:rgba(139,92,246,.2);
                animation: markerPulse 1.2s infinite;
            }}

            .complete .agent-marker {{
                color:#86efac;
                background:rgba(34,197,94,.14);
            }}

            .agent-icon {{
                font-size:1rem;
                width:25px;
                text-align:center;
                filter:saturate(1.15);
            }}

            .agent-copy {{
                min-width:0;
                flex:1;
            }}

            .agent-name {{
                color:#e2e8f0;
                font-size:.78rem;
                font-weight:750;
            }}

            .agent-description {{
                color:#64748b;
                font-size:.67rem;
                margin-top:.12rem;
            }}

            .agent-status {{
                color:#64748b;
                font-size:.62rem;
                font-weight:800;
                text-transform:uppercase;
                letter-spacing:.06em;
            }}

            .active .agent-status {{
                color:#c4b5fd;
            }}

            .complete .agent-status {{
                color:#86efac;
            }}

            .agent-current {{
                margin-top:1rem;
                padding:.72rem .9rem;
                border-radius:13px;
                color:#a5b4fc;
                background:rgba(99,102,241,.07);
                border:1px solid rgba(99,102,241,.12);
                font-size:.72rem;
                text-align:center;
            }}

            @keyframes agentPulse {{
                0%,100% {{ transform:scale(1); box-shadow:0 0 0 6px rgba(139,92,246,.08), 0 0 30px rgba(139,92,246,.25); }}
                50% {{ transform:scale(1.04); box-shadow:0 0 0 9px rgba(139,92,246,.04), 0 0 45px rgba(168,85,247,.42); }}
            }}

            @keyframes dotPulse {{
                0%,100% {{ opacity:.35; transform:scale(.8); }}
                50% {{ opacity:1; transform:scale(1.15); }}
            }}

            @keyframes markerPulse {{
                0%,100% {{ box-shadow:0 0 0 0 rgba(139,92,246,.25); }}
                50% {{ box-shadow:0 0 0 5px rgba(139,92,246,0); }}
            }}
        </style>

        <div class="agent-shell">
            <div class="agent-header">
                <div class="agent-orb">✦</div>
                <div>
                    <div class="agent-title">Meeting Copilot is thinking</div>
                    <div class="agent-subtitle">Multiple AI agents are turning your conversation into structured intelligence.</div>
                </div>
                <div class="agent-live">Live</div>
            </div>

            <div class="agent-steps">
                {''.join(cards)}
            </div>

            <div class="agent-current">
                ✦ Currently working: <strong>{current_name}</strong>
            </div>
        </div>
        """,
    )


def generate_meeting_mom(
    meeting_id: int,
) -> dict | None:
    """
    Generate Minutes of Meeting through the FastAPI backend.

    The backend builds the MoM from the meeting metadata
    and the AI analysis already stored in PostgreSQL.
    """

    try:
        client = APIClient()

        response = requests.post(
            f"{client.base_url}/meetings/{meeting_id}/mom",
            timeout=60,
        )

        response.raise_for_status()

        mom = response.json()

        st.session_state[
            "mom"
        ] = mom

        return mom

    except Exception as exc:
        st.session_state[
            "mom"
        ] = None

        st.warning(
            f"Minutes of Meeting could not be generated: {exc}"
        )

        return None



def generate_mom_export(
    mom: dict,
    export_format: str,
) -> tuple[bytes, str, str]:
    """Generate an export file for a Minutes of Meeting object.

    Args:
        mom: MoM response returned by the FastAPI backend.
        export_format: One of ``txt``, ``docx``, or ``pdf``.

    Returns:
        Tuple containing file bytes, download filename, and MIME type.
    """

    mom_model = MinutesOfMeeting.model_validate(mom)
    meeting_id = mom_model.meeting_id

    export_directory = Path("exports")
    export_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    if export_format == "txt":
        output_path = (
            export_directory
            / f"meeting_{meeting_id}_mom.txt"
        )

        TXTExporter().export(
            mom=mom_model,
            output_path=output_path,
        )

        return (
            output_path.read_bytes(),
            output_path.name,
            "text/plain",
        )

    if export_format == "docx":
        output_path = (
            export_directory
            / f"meeting_{meeting_id}_mom.docx"
        )

        DOCXExporter().export(
            mom=mom_model,
            output_path=output_path,
        )

        return (
            output_path.read_bytes(),
            output_path.name,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    if export_format == "pdf":
        output_path = (
            export_directory
            / f"meeting_{meeting_id}_mom.pdf"
        )

        PDFExporter().export(
            mom=mom_model,
            output_path=output_path,
        )

        return (
            output_path.read_bytes(),
            output_path.name,
            "application/pdf",
        )

    raise ValueError(
        f"Unsupported export format: {export_format}"
    )

def handle_end_meeting() -> bool:
    """
    End the active meeting, save the recording,
    generate the transcript, and generate AI analysis.
    """

    meeting_id = st.session_state.get(
        "meeting_id"
    )

    if meeting_id is None:

        st.error(
            "No active meeting was found."
        )

        return False

    client = APIClient()
    processing_container = st.empty()

    try:

        # --------------------------------------------------
        # AGENT 1 — RECORDING
        # --------------------------------------------------

        render_agentic_processing(
            processing_container,
            active_step=1,
        )

        meeting = client.end_meeting(
            meeting_id
        )

        st.session_state[
            "meeting_active"
        ] = False

        st.session_state[
            "audio_path"
        ] = meeting.get(
            "audio_path"
        )

        st.session_state[
            "completed_duration_seconds"
        ] = meeting.get(
            "duration_seconds",
            0,
        ) or 0

        st.session_state[
            "recording_started_at"
        ] = None

        st.session_state[
            "meeting_paused"
        ] = False

        st.session_state[
            "active_duration_before_pause"
        ] = 0

        st.session_state[
            "pause_started_at"
        ] = None

        st.session_state[
            "audio_level"
        ] = 0.0

        # --------------------------------------------------
        # AGENT 2 — TRANSCRIPTION
        # --------------------------------------------------

        render_agentic_processing(
            processing_container,
            active_step=2,
            completed_steps={1},
        )

        transcript = client.transcribe_meeting(
            meeting_id
        )

        st.session_state[
            "transcript"
        ] = transcript.get(
            "full_text",
            "",
        )

        st.session_state[
            "word_timestamps"
        ] = transcript.get(
            "word_timestamps",
            [],
        )

        # --------------------------------------------------
        # SPEAKER DIARIZATION + TRANSCRIPT ALIGNMENT
        # --------------------------------------------------

        # # Speaker diarization is part of the transcription stage.
        # # If it fails, keep the normal transcript and continue
        # # with AI analysis instead of failing the entire meeting.
        # try:
        #     client.diarize_meeting(
        #         meeting_id
        #     )

        #     st.session_state[
        #         "speaker_transcript"
        #     ] = client.get_speaker_transcript(
        #         meeting_id
        #     )

        # except Exception as exc:
        #     st.session_state[
        #         "speaker_transcript"
        #     ] = None

        #     st.warning(
        #         "Speaker diarization could not be completed. "
        #         f"The standard transcript is still available. ({exc})"
        #     )

        # --------------------------------------------------
        # AGENT 3 — INTELLIGENCE
        # --------------------------------------------------

        render_agentic_processing(
            processing_container,
            active_step=3,
            completed_steps={1, 2},
        )

        analysis = client.analyze_meeting(
            meeting_id
        )

        st.session_state[
            "analysis"
        ] = analysis

        # --------------------------------------------------
        # AGENT 4 — MINUTES OF MEETING
        # --------------------------------------------------

        render_agentic_processing(
            processing_container,
            active_step=4,
            completed_steps={1, 2, 3},
        )

        generate_meeting_mom(
            meeting_id
        )

        # --------------------------------------------------
        # AGENT 5 — MEMORY / PERSISTENCE
        # --------------------------------------------------

        render_agentic_processing(
            processing_container,
            active_step=5,
            completed_steps={1, 2, 3, 4},
        )

        # The analysis endpoint has already persisted the
        # generated intelligence in PostgreSQL. This final
        # visual stage represents that completed persistence
        # step without making another database/API request.

        render_agentic_processing(
            processing_container,
            active_step=5,
            completed_steps={1, 2, 3, 4},
        )

        time.sleep(0.35)
        processing_container.empty()

        return True

    except Exception as exc:

        processing_container.empty()

        st.error(
            f"Unable to complete meeting: {exc}"
        )

        return False


def render_meeting_controls() -> bool:
    """
    Render Pause/Resume and End controls.

    Returns:
        bool: True when End Meeting is clicked.
    """

    is_paused = st.session_state.get(
        "meeting_paused",
        False,
    )

    pause_column, end_column = (
        st.columns(
            [1, 1]
        )
    )

    with pause_column:

        if is_paused:

            resume_clicked = st.button(
                "▶️  Resume Meeting",
                use_container_width=True,
                key="resume_meeting_button",
            )

            if resume_clicked:

                if handle_resume_meeting():

                    st.rerun()

        else:

            pause_clicked = st.button(
                "⏸️  Pause Meeting",
                use_container_width=True,
                key="pause_meeting_button",
            )

            if pause_clicked:

                if handle_pause_meeting():

                    st.rerun()

    with end_column:

        end_clicked = st.button(
            "⏹️  End Meeting",
            use_container_width=True,
            key="end_meeting_button",
        )

        if end_clicked:

            return True

    return False


def render_completed_meeting() -> None:
    """Render the completed meeting screen."""

    # Allow the user to leave the completed-meeting view
    # and return to the dashboard homepage.
    home_column, _ = st.columns([1, 5])

    with home_column:
        if st.button(
            "🏠 Back to Home",
            use_container_width=True,
            key="completed_back_to_home_button",
        ):
            go_to_home()
            st.rerun()

    transcript = st.session_state.get(
        "transcript"
    )

    audio_path = st.session_state.get(
        "audio_path"
    )

    word_timestamps = (
        st.session_state.get(
            "word_timestamps",
            [],
        )
    )

    speaker_transcript = st.session_state.get(
        "speaker_transcript"
    )

    duration_seconds = (
        st.session_state.get(
            "completed_duration_seconds",
            0,
        )
    )

    # --------------------------------------------------
    # RECOVER STORED AI RESULTS
    # --------------------------------------------------
    #
    # The backend persists analysis and MoM independently.
    # If a Streamlit request is interrupted during the
    # long-running processing workflow, recover the already
    # generated results from FastAPI instead of showing an
    # empty AI section.
    # --------------------------------------------------

    meeting_id = st.session_state.get(
        "meeting_id"
    )

    client = APIClient()

    if meeting_id is not None:

        if not st.session_state.get("analysis"):
            try:
                st.session_state[
                    "analysis"
                ] = client.get_meeting_analysis(
                    int(meeting_id)
                )
            except requests.HTTPError:
                pass
            except Exception:
                pass

        if not st.session_state.get("mom"):
            try:
                mom_response = requests.get(
                    f"{client.base_url}/meetings/{meeting_id}/mom",
                    timeout=30,
                )
                mom_response.raise_for_status()
                st.session_state[
                    "mom"
                ] = mom_response.json()
            except requests.HTTPError:
                pass
            except Exception:
                pass

        if not st.session_state.get("speaker_transcript"):
            try:
                st.session_state[
                    "speaker_transcript"
                ] = client.get_speaker_transcript(
                    int(meeting_id)
                )
            except requests.HTTPError:
                pass
            except Exception:
                pass

    speaker_transcript = st.session_state.get(
        "speaker_transcript"
    )

    analysis = st.session_state.get(
        "analysis"
    )

    render_completed_banner()

    render_meeting_metrics(
        duration=format_duration(
            duration_seconds
        ),
        words=len(
            (transcript or "").split()
        ),
        participants=len(
            (speaker_transcript or {}).get(
                "speakers",
                [],
            )
        ),
    )

    st.divider()

    left_column, right_column = (
        st.columns(2)
    )

    with left_column:

        st.html(
            """
            <div class="content-title">
                📝 Synchronized Transcript
            </div>
            """
        )

        if (
            audio_path
            and word_timestamps
        ):

            render_synced_audio_transcript(
                audio_path=audio_path,
                words=word_timestamps,
            )

        else:

            render_transcript_panel(
                transcript=transcript or ""
            )

        if speaker_transcript:
            st.divider()
            render_speaker_transcript(
                speaker_transcript
            )

    with right_column:

        render_insights_panel()

    # ==================================================
    # AI MEETING INTELLIGENCE
    # ==================================================

    if analysis:

        st.divider()

        st.html(
            """
            <div class="content-title">
                🧠 AI Meeting Intelligence
            </div>
            """
        )

        # --------------------------------------------------
        # SUMMARY
        # --------------------------------------------------

        st.markdown(
            "### ✨ Summary"
        )

        summary = analysis.get(
            "summary",
            "No summary available.",
        )

        st.info(summary)

        # --------------------------------------------------
        # KEY POINTS + DECISIONS
        # --------------------------------------------------

        key_points_column, decisions_column = (
            st.columns(2)
        )

        with key_points_column:

            st.markdown(
                "### 💡 Key Points"
            )

            key_points = analysis.get(
                "key_points",
                [],
            )

            if key_points:

                for point in key_points:

                    st.markdown(
                        f"- {point}"
                    )

            else:

                st.caption(
                    "No key points identified."
                )

        with decisions_column:

            st.markdown(
                "### ✅ Decisions"
            )

            decisions = analysis.get(
                "decisions",
                [],
            )

            if decisions:

                for decision in decisions:

                    st.markdown(
                        f"- {decision}"
                    )

            else:

                st.caption(
                    "No decisions identified."
                )

        # --------------------------------------------------
        # ACTION ITEMS
        # --------------------------------------------------

        st.markdown(
            "### 📋 Action Items"
        )

        action_items = analysis.get(
            "action_items",
            [],
        )

        if action_items:

            for index, item in enumerate(
                action_items,
                start=1,
            ):

                task = item.get(
                    "task",
                    "Unnamed task",
                )

                assignee = item.get(
                    "assignee"
                ) or "Unassigned"

                deadline = item.get(
                    "deadline"
                ) or "No deadline"

                priority = item.get(
                    "priority",
                    "medium",
                )

                st.markdown(
                    f"""
**{index}. {task}**

👤 **Assignee:** {assignee}  
📅 **Deadline:** {deadline}  
🎯 **Priority:** {priority}
"""
                )

                if index < len(
                    action_items
                ):

                    st.divider()

        else:

            st.caption(
                "No action items identified."
            )

        # --------------------------------------------------
        # NEXT STEPS
        # --------------------------------------------------

        st.markdown(
            "### 🚀 Next Steps"
        )

        next_steps = analysis.get(
            "next_steps",
            [],
        )

        if next_steps:

            for step in next_steps:

                st.markdown(
                    f"- {step}"
                )

        else:

            st.caption(
                "No next steps identified."
            )

    else:

        st.info(
            "AI analysis is not available for "
            "this meeting."
        )

    # ==================================================
    # MINUTES OF MEETING
    # ==================================================

    mom = st.session_state.get(
        "mom"
    )

    if mom:

        st.divider()

        st.html(
            """
            <div class="content-title">
                📋 Minutes of Meeting
            </div>
            """
        )

        # --------------------------------------------------
        # MEETING INFORMATION
        # --------------------------------------------------

        meeting_date = mom.get(
            "meeting_date"
        )

        if meeting_date:
            meeting_date_text = format_local_datetime(
                meeting_date
            )
        else:
            meeting_date_text = "Not available"

        mom_duration = mom.get(
            "duration_seconds"
        )

        info_columns = st.columns(
            3
        )

        with info_columns[0]:
            st.markdown(
                "**Meeting**"
            )
            st.write(
                mom.get(
                    "meeting_title",
                    "Untitled Meeting",
                )
            )

        with info_columns[1]:
            st.markdown(
                "**Date**"
            )
            st.write(
                meeting_date_text
            )

        with info_columns[2]:
            st.markdown(
                "**Duration**"
            )
            st.write(
                format_duration(
                    int(mom_duration)
                )
                if mom_duration is not None
                else "Not available"
            )

        st.divider()

        # --------------------------------------------------
        # EXECUTIVE SUMMARY
        # --------------------------------------------------

        st.markdown(
            "### 📝 Executive Summary"
        )

        st.info(
            mom.get(
                "summary",
                "No summary available.",
            )
        )

        # --------------------------------------------------
        # DECISIONS
        # --------------------------------------------------

        decisions = mom.get(
            "decisions",
            [],
        )

        st.markdown(
            "### ✅ Decisions"
        )

        if decisions:

            for index, decision in enumerate(
                decisions,
                start=1,
            ):
                st.markdown(
                    f"**{index}.** {decision}"
                )

        else:
            st.caption(
                "No decisions were recorded for this meeting."
            )

        # --------------------------------------------------
        # ACTION ITEMS
        # --------------------------------------------------

        st.markdown(
            "### 📋 Action Items"
        )

        mom_action_items = mom.get(
            "action_items",
            [],
        )

        if mom_action_items:

            for index, item in enumerate(
                mom_action_items,
                start=1,
            ):

                task = item.get(
                    "task",
                    "Unnamed task",
                )

                assignee = item.get(
                    "assignee"
                ) or "Unassigned"

                deadline = item.get(
                    "deadline"
                ) or "No deadline"

                priority = item.get(
                    "priority",
                    "medium",
                ).title()

                action_column, details_column = (
                    st.columns([3, 2])
                )

                with action_column:
                    st.markdown(
                        f"**{index}. {task}**"
                    )

                with details_column:
                    st.caption(
                        f"👤 {assignee}   •   "
                        f"📅 {deadline}   •   "
                        f"🎯 {priority}"
                    )

                if index < len(
                    mom_action_items
                ):
                    st.divider()

        else:
            st.caption(
                "No action items were recorded for this meeting."
            )

        # --------------------------------------------------
        # NEXT STEPS
        # --------------------------------------------------

        next_steps = mom.get(
            "next_steps",
            [],
        )

        st.markdown(
            "### 🚀 Next Steps"
        )

        if next_steps:

            for index, step in enumerate(
                next_steps,
                start=1,
            ):
                st.markdown(
                    f"**{index}.** {step}"
                )

        else:
            st.caption(
                "No next steps were recorded for this meeting."
            )

    # ==================================================
    # EXPORT MINUTES OF MEETING
    # ==================================================

    if mom:

        st.divider()

        st.markdown(
            "### 📤 Export Minutes of Meeting"
        )

        st.caption(
            "Download the generated Minutes of Meeting in your preferred format."
        )

        export_columns = st.columns(3)

        export_options = [
            (
                export_columns[0],
                "📄 Download TXT",
                "txt",
            ),
            (
                export_columns[1],
                "📝 Download DOCX",
                "docx",
            ),
            (
                export_columns[2],
                "📕 Download PDF",
                "pdf",
            ),
        ]

        for column, label, export_format in export_options:
            with column:
                try:
                    file_data, file_name, mime_type = generate_mom_export(
                        mom,
                        export_format,
                    )

                    st.download_button(
                        label=label,
                        data=file_data,
                        file_name=file_name,
                        mime=mime_type,
                        use_container_width=True,
                        key=(
                            f"download_mom_{export_format}_"
                            f"{mom.get('meeting_id')}"
                        ),
                    )

                except Exception as exc:
                    st.error(
                        f"Unable to prepare {export_format.upper()} export: {exc}"
                    )

    else:

        st.divider()

        st.markdown(
            "### 📤 Export Minutes of Meeting"
        )

        st.info(
            "Minutes of Meeting are not available yet. "
            "Generate the meeting intelligence first."
        )

    # ==================================================
    # MEETING RECORDING
    # ==================================================

    st.divider()

    st.html(
        """
        <div class="content-title">
            🎙️ Meeting Recording
        </div>
        """
    )

    if audio_path:

        st.info(
            "Use the synchronized player above "
            "to listen and follow the transcript."
        )

    else:

        st.warning(
            "No recording is available."
        )


def load_historical_meeting(
    meeting_id: int,
) -> bool:
    """
    Load a previously stored meeting into the dashboard state.

    Historical data is retrieved through FastAPI rather than
    accessing PostgreSQL directly from Streamlit.
    """

    try:
        client = APIClient()

        meeting = client.get_meeting(
            meeting_id
        )

        transcript = None
        analysis = None
        speaker_transcript = None

        try:
            transcript = (
                client.get_meeting_transcript(
                    meeting_id
                )
            )
        except requests.HTTPError:
            transcript = None

        try:
            analysis = (
                client.get_meeting_analysis(
                    meeting_id
                )
            )
        except requests.HTTPError:
            analysis = None

        try:
            speaker_transcript = (
                client.get_speaker_transcript(
                    meeting_id
                )
            )
        except requests.HTTPError:
            speaker_transcript = None
        except Exception:
            speaker_transcript = None

        st.session_state[
            "selected_history_meeting_id"
        ] = meeting_id

        st.session_state[
            "meeting_id"
        ] = meeting.get("id")

        st.session_state[
            "meeting_title"
        ] = meeting.get("title")

        st.session_state[
            "audio_path"
        ] = meeting.get("audio_path")

        st.session_state[
            "completed_duration_seconds"
        ] = (
            meeting.get("duration_seconds")
            or 0
        )

        st.session_state[
            "transcript"
        ] = (
            transcript.get("full_text", "")
            if transcript
            else None
        )

        st.session_state[
            "word_timestamps"
        ] = (
            transcript.get(
                "word_timestamps",
                [],
            )
            if transcript
            else []
        )

        st.session_state[
            "speaker_transcript"
        ] = speaker_transcript

        st.session_state[
            "analysis"
        ] = analysis

        # Generate the structured MoM from the stored
        # meeting analysis when viewing a historical meeting.
        if analysis:
            generate_meeting_mom(
                meeting_id
            )
        else:
            st.session_state[
                "mom"
            ] = None

        return True

    except Exception as exc:
        st.error(
            f"Unable to load meeting #{meeting_id}: {exc}"
        )
        return False


def clear_historical_meeting() -> None:
    """
    Clear the selected historical meeting from the dashboard state.
    """

    st.session_state[
        "selected_history_meeting_id"
    ] = None

    st.session_state[
        "meeting_id"
    ] = None

    st.session_state[
        "meeting_title"
    ] = None

    st.session_state[
        "audio_path"
    ] = None

    st.session_state[
        "transcript"
    ] = None

    st.session_state[
        "word_timestamps"
    ] = []

    st.session_state[
        "speaker_transcript"
    ] = None

    st.session_state[
        "completed_duration_seconds"
    ] = 0

    st.session_state[
        "analysis"
    ] = None

    st.session_state[
        "mom"
    ] = None


def go_to_home() -> None:
    """
    Return from a historical meeting to the dashboard homepage.
    """

    clear_historical_meeting()

    st.session_state[
        "meeting_history_visible_count"
    ] = 10

    st.session_state[
        "meeting_history_search"
    ] = ""

    st.session_state[
        "meeting_history_date"
    ] = None


def render_historical_meeting_view() -> None:
    """
    Render the existing completed-meeting presentation
    for a selected historical meeting.
    """

    selected_id = st.session_state.get(
        "selected_history_meeting_id"
    )

    if selected_id is None:
        return

    meeting_title = (
        st.session_state.get(
            "meeting_title"
        )
        or "Meeting"
    )

    back_column, home_column = st.columns(2)

    with back_column:
        if st.button(
            "← Back to Meeting History",
            use_container_width=True,
            key="back_to_meeting_history_button",
        ):
            clear_historical_meeting()
            st.rerun()

    with home_column:
        if st.button(
            "🏠 Back to Home",
            use_container_width=True,
            key="back_to_home_button",
        ):
            go_to_home()
            st.rerun()

    st.html(
        f"""
        <div style="
            text-align:center;
            margin:0.8rem 0 1rem 0;
            color:#94a3b8;
            font-size:0.8rem;
        ">
            🎙️ Viewing saved meeting #{selected_id}
        </div>
        """
    )

    st.markdown(
        f"## {meeting_title}"
    )

    render_completed_meeting()


def render_meeting_history() -> None:
    """Render previously saved meetings from PostgreSQL."""

    st.divider()

    st.html(
        """
        <div class="content-title">
            🗂️ Meeting History
        </div>
        """
    )

    try:
        client = APIClient()
        meetings = client.get_all_meetings()
    except Exception as exc:
        st.warning(f"Unable to load meeting history: {exc}")
        return

    if not meetings:
        st.caption("No previous meetings have been recorded yet.")
        return

    st.caption(
        f"{len(meetings)} meeting{'' if len(meetings) == 1 else 's'} stored in your meeting history."
    )

    # --------------------------------------------------
    # SEARCH / DATE FILTER
    # --------------------------------------------------

    search_column, date_column = st.columns([2, 1])

    with search_column:
        search_query = st.text_input(
            "🔎 Search meetings",
            placeholder="Search by meeting title or ID...",
            key="meeting_history_search",
        )

    with date_column:
        selected_date = st.date_input(
            "📅 Filter by date",
            value=None,
            key="meeting_history_date",
        )

    # Search across the complete history, not only the
    # currently visible batch.
    filtered_meetings = meetings

    if search_query.strip():
        query = search_query.strip().lower()

        filtered_meetings = [
            meeting
            for meeting in filtered_meetings
            if (
                query in str(meeting.get("id", "")).lower()
                or query in str(
                    meeting.get("title", "")
                ).lower()
            )
        ]

    if selected_date is not None:
        filtered_meetings = [
            meeting
            for meeting in filtered_meetings
            if (
                meeting.get("created_at")
                and datetime.fromisoformat(
                    meeting["created_at"].replace(
                        "Z",
                        "+00:00",
                    )
                ).astimezone(LOCAL_TIMEZONE).date()
                == selected_date
            )
        ]

    # Keep the history compact by showing only a small batch
    # at a time. Older meetings are revealed with Load More.
    page_size = 10

    if (
        "meeting_history_visible_count" not in st.session_state
        or st.session_state.get(
            "meeting_history_last_filter"
        )
        != (
            search_query.strip().lower(),
            str(selected_date),
        )
    ):
        st.session_state[
            "meeting_history_visible_count"
        ] = page_size

        st.session_state[
            "meeting_history_last_filter"
        ] = (
            search_query.strip().lower(),
            str(selected_date),
        )

    if not filtered_meetings:
        st.info(
            "No meetings match your search or selected date."
        )
        return

    st.caption(
        f"Showing {min(page_size, len(filtered_meetings))} "
        f"of {len(filtered_meetings)} matching meeting"
        f"{'' if len(filtered_meetings) == 1 else 's'}."
    )

    visible_count = int(
        st.session_state["meeting_history_visible_count"]
    )

    visible_meetings = filtered_meetings[:visible_count]

    for meeting in visible_meetings:
        meeting_id = meeting.get("id")
        title = meeting.get("title", "Untitled Meeting")
        duration_seconds = meeting.get("duration_seconds")
        created_at = meeting.get("created_at")
        ended_at = meeting.get("ended_at")
        audio_path = meeting.get("audio_path")

        duration_text = (
            format_duration(int(duration_seconds))
            if duration_seconds is not None
            else "Not completed"
        )

        if ended_at and audio_path:
            status_text = "Completed"
        elif ended_at:
            status_text = "Completed • No recording"
        else:
            status_text = "Incomplete"

        date_text = (
            format_local_datetime(created_at)
            if created_at
            else "Unknown date"
        )

        with st.expander(
            f"🎙️  {title}  •  #{meeting_id}",
            expanded=False,
        ):
            detail_column, status_column = st.columns([2, 1])

            with detail_column:
                st.markdown(f"**Recorded:** {date_text}")
                st.markdown(f"**Duration:** {duration_text}")

            with status_column:
                st.markdown(f"**Status:** {status_text}")

            if st.button(
                "View Meeting",
                use_container_width=True,
                key=f"view_history_meeting_{meeting_id}",
            ):
                if load_historical_meeting(
                    int(meeting_id)
                ):
                    st.rerun()

    # Reveal the next batch only when requested.
    if visible_count < len(filtered_meetings):
        remaining = len(filtered_meetings) - visible_count
        next_count = min(page_size, remaining)

        if st.button(
            f"Load More Meetings ({next_count})",
            use_container_width=True,
            key="load_more_meetings_button",
        ):
            st.session_state[
                "meeting_history_visible_count"
            ] = visible_count + page_size

            st.rerun()



RAG_BOT_AVATAR_DATA_URI = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMjggMTI4Ij48ZGVmcz48bGluZWFyR3JhZGllbnQgaWQ9ImciIHgxPSIwIiB5MT0iMCIgeDI9IjEiIHkyPSIxIj48c3RvcCBvZmZzZXQ9IjAiIHN0b3AtY29sb3I9IiM2ZDVkZmMiLz48c3RvcCBvZmZzZXQ9IjEiIHN0b3AtY29sb3I9IiNhODU1ZjciLz48L2xpbmVhckdyYWRpZW50PjxsaW5lYXJHcmFkaWVudCBpZD0iYiIgeDE9IjAiIHkxPSIwIiB4Mj0iMSIgeTI9IjEiPjxzdG9wIG9mZnNldD0iMCIgc3RvcC1jb2xvcj0iI2RmZjRmZiIvPjxzdG9wIG9mZnNldD0iMSIgc3RvcC1jb2xvcj0iIzlmZGNmZiIvPjwvbGluZWFyR3JhZGllbnQ+PC9kZWZzPjxjaXJjbGUgY3g9IjY0IiBjeT0iNjQiIHI9IjYxIiBmaWxsPSJ1cmwoI2cpIi8+PGNpcmNsZSBjeD0iNjQiIGN5PSI2NCIgcj0iNTYiIGZpbGw9IiMxNzFjM2IiIHN0cm9rZT0iI2E3OGJmYSIgc3Ryb2tlLXdpZHRoPSIzIi8+PHJlY3QgeD0iMjciIHk9IjQzIiB3aWR0aD0iNzQiIGhlaWdodD0iNTQiIHJ4PSIxOCIgZmlsbD0idXJsKCNiKSIgc3Ryb2tlPSIjZmZmZmZmIiBzdHJva2Utd2lkdGg9IjQiLz48cmVjdCB4PSIzNCIgeT0iNTAiIHdpZHRoPSI2MCIgaGVpZ2h0PSI0MCIgcng9IjEzIiBmaWxsPSIjMjQzMDUyIi8+PGNpcmNsZSBjeD0iNTEiIGN5PSI2OSIgcj0iNyIgZmlsbD0iI2Q5ZjRmZiIvPjxjaXJjbGUgY3g9Ijc3IiBjeT0iNjkiIHI9IjciIGZpbGw9IiNkOWY0ZmYiLz48Y2lyY2xlIGN4PSI1MSIgY3k9IjY5IiByPSIzIiBmaWxsPSIjNjM2NmYxIi8+PGNpcmNsZSBjeD0iNzciIGN5PSI2OSIgcj0iMyIgZmlsbD0iIzYzNjZmMSIvPjxwYXRoIGQ9Ik01MiA4MCBRNjQgODggNzYgODAiIGZpbGw9Im5vbmUiIHN0cm9rZT0iI2Q5ZjRmZiIgc3Ryb2tlLXdpZHRoPSI0IiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48cmVjdCB4PSIxMyIgeT0iNTYiIHdpZHRoPSIxNSIgaGVpZ2h0PSIyOCIgcng9IjciIGZpbGw9IiM5ZmRjZmYiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIzIi8+PHJlY3QgeD0iMTAwIiB5PSI1NiIgd2lkdGg9IjE1IiBoZWlnaHQ9IjI4IiByeD0iNyIgZmlsbD0iIzlmZGNmZiIgc3Ryb2tlPSIjZmZmIiBzdHJva2Utd2lkdGg9IjMiLz48cGF0aCBkPSJNNjQgNDNWMzAiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSI0IiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48Y2lyY2xlIGN4PSI2NCIgY3k9IjI1IiByPSI3IiBmaWxsPSIjYTc4YmZhIiBzdHJva2U9IiNmZmYiIHN0cm9rZS13aWR0aD0iMyIvPjxjaXJjbGUgY3g9IjEwMyIgY3k9IjEwNSIgcj0iMTEiIGZpbGw9IiMyMmM1NWUiIHN0cm9rZT0iIzE3MWMzYiIgc3Ryb2tlLXdpZHRoPSI1Ii8+PC9zdmc+"


def render_rag_assistant() -> None:
    """Render the floating AI Meeting Assistant with a true inner chat scroll area."""

    if "rag_messages" not in st.session_state:
        st.session_state["rag_messages"] = [
            {
                "role": "assistant",
                "content": (
                    "Hi! I'm your AI Meeting Assistant. "
                    "I can help you find information from your meeting transcripts, "
                    "answer questions, and summarize discussions."
                ),
                "sources": [],
            }
        ]

    if "rag_question_input" not in st.session_state:
        st.session_state["rag_question_input"] = ""

    if "rag_assistant_open" not in st.session_state:
        st.session_state["rag_assistant_open"] = False

    if "rag_show_quick_questions" not in st.session_state:
        st.session_state["rag_show_quick_questions"] = True

    # --------------------------------------------------
    # FLOATING BOT + FIXED CHAT PANEL
    # --------------------------------------------------

    st.markdown(
        f"""
        <style>
        /* ==============================================
           FLOATING ROBOT
           ============================================== */

        div.st-key-rag_floating_button {{
            position: fixed !important;
            right: 28px !important;
            bottom: 24px !important;
            width: 76px !important;
            height: 76px !important;
            min-width: 76px !important;
            max-width: 76px !important;
            min-height: 76px !important;
            max-height: 76px !important;
            margin: 0 !important;
            padding: 0 !important;
            z-index: 2147483647 !important;
            background: transparent !important;
            overflow: visible !important;
        }}

        div.st-key-rag_floating_button button {{
            width: 76px !important;
            height: 76px !important;
            min-width: 76px !important;
            min-height: 76px !important;
            padding: 0 !important;
            margin: 0 !important;
            border: 0 !important;
            border-radius: 50% !important;
            background-color: transparent !important;
            background-image: url("{RAG_BOT_AVATAR_DATA_URI}") !important;
            background-repeat: no-repeat !important;
            background-position: center !important;
            background-size: contain !important;
            color: transparent !important;
            font-size: 0 !important;
            box-shadow: 0 10px 32px rgba(92,62,230,.48) !important;
            cursor: pointer !important;
            transition: transform .18s ease, box-shadow .18s ease !important;
        }}

        div.st-key-rag_floating_button button:hover {{
            transform: scale(1.08) !important;
            box-shadow: 0 14px 42px rgba(92,62,230,.68) !important;
        }}

        /* ==============================================
           CHAT PANEL
           ============================================== */

        /* The key container itself is the fixed panel. */
        div.st-key-rag_chat_panel {{
            position: fixed !important;
            right: 28px !important;
            bottom: 112px !important;
            width: 400px !important;
            max-width: calc(100vw - 32px) !important;
            height: 680px !important;
            max-height: calc(100vh - 140px) !important;
            margin: 0 !important;
            padding: 0 !important;
            z-index: 2147483646 !important;
            border: 1px solid rgba(139,92,246,.42) !important;
            border-radius: 20px !important;
            background: #050a19 !important;
            box-shadow: 0 24px 70px rgba(0,0,0,.62), 0 0 0 1px rgba(255,255,255,.04) inset !important;
            overflow: hidden !important;
        }}

        /* Do NOT force overflow:visible on the panel descendants.
           Streamlit's height container needs its own overflow:auto. */
        div.st-key-rag_chat_panel > div {{
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
        }}

        div.st-key-rag_chat_panel > div > div {{
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
        }}

        /* ==============================================
           HEADER
           ============================================== */

        div.st-key-rag_chat_panel .rag-assistant-header {{
            display: flex;
            align-items: center;
            width: 100%;
            min-height: 58px;
        }}

        /* ==============================================
           QUICK QUESTIONS
           ============================================== */

        div.st-key-rag_quick_questions {{
            width: 100% !important;
            box-sizing: border-box !important;
        }}

        div.st-key-rag_quick_questions button {{
            min-height: 46px !important;
            height: 46px !important;
            border-radius: 11px !important;
            padding: 0 12px !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }}

        /* ==============================================
           TRUE INNER CHAT SCROLLER
           ============================================== */

        /* st.container(height=...) creates this wrapper in Streamlit. */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-rag_chat_history) {{
            height: 100% !important;
            min-height: 0 !important;
            max-height: 100% !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
            box-sizing: border-box !important;
            scrollbar-width: thin !important;
            scrollbar-color: rgba(148,163,184,.55) transparent !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-rag_chat_history)::-webkit-scrollbar {{
            width: 7px !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-rag_chat_history)::-webkit-scrollbar-track {{
            background: transparent !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-rag_chat_history)::-webkit-scrollbar-thumb {{
            background: rgba(148,163,184,.55) !important;
            border-radius: 10px !important;
        }}

        div.st-key-rag_chat_history {{
            width: 100% !important;
            box-sizing: border-box !important;
            min-height: 0 !important;
            padding: 6px !important;
            margin: 0 !important;
            background: rgba(15,23,42,.20) !important;
        }}

        div.st-key-rag_chat_history [data-testid="stChatMessage"] {{
            margin-top: 3px !important;
            margin-bottom: 10px !important;
        }}

        /* ==============================================
           INPUT FORM
           ============================================== */

        div.st-key-rag_chat_input_form {{
            width: 100% !important;
            box-sizing: border-box !important;
            margin: 0 !important;
            padding: 8px 0 0 0 !important;
            border: 0 !important;
            background: transparent !important;
        }}

        div.st-key-rag_chat_input_form [data-testid="column"] {{
            padding: 0 !important;
        }}

        div.st-key-rag_chat_input_form div[data-testid="stTextInput"] {{
            margin: 0 !important;
        }}

        div.st-key-rag_chat_input_form div[data-testid="stTextInput"] input {{
            width: 100% !important;
            height: 48px !important;
            min-height: 48px !important;
            box-sizing: border-box !important;
            border-radius: 13px !important;
            padding: 0 14px !important;
            background: #171b2a !important;
            border: 1px solid rgba(148,163,184,.22) !important;
        }}

        div.st-key-rag_chat_input_form div[data-testid="stFormSubmitButton"] {{
            width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
        }}

        div.st-key-rag_chat_input_form div[data-testid="stFormSubmitButton"] button {{
            width: 52px !important;
            min-width: 52px !important;
            max-width: 52px !important;
            height: 48px !important;
            min-height: 48px !important;
            max-height: 48px !important;
            padding: 0 !important;
            margin: 0 !important;
            border-radius: 13px !important;
            font-size: 21px !important;
            line-height: 1 !important;
        }}

        /* ==============================================
           FOOTER
           ============================================== */

        div.st-key-rag_chat_panel .rag-assistant-footer {{
            text-align: center;
            color: #64748b;
            font-size: .67rem;
            margin: 7px 0 4px 0;
            line-height: 1.2;
        }}

        @media (max-width: 600px) {{
            div.st-key-rag_floating_button {{
                right: 16px !important;
                bottom: 16px !important;
            }}

            div.st-key-rag_chat_panel {{
                right: 16px !important;
                bottom: 102px !important;
                width: calc(100vw - 32px) !important;
                max-width: calc(100vw - 32px) !important;
                height: calc(100vh - 120px) !important;
                max-height: calc(100vh - 120px) !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------
    # FLOATING ROBOT
    # --------------------------------------------------

    with st.container(key="rag_floating_button"):
        if st.button(
            "AI",
            key="rag_open_button",
            help="Ask about your meetings",
            use_container_width=True,
        ):
            st.session_state["rag_assistant_open"] = not st.session_state["rag_assistant_open"]
            st.rerun()

    if not st.session_state["rag_assistant_open"]:
        return

    # --------------------------------------------------
    # CHAT PANEL
    # --------------------------------------------------

    with st.container(key="rag_chat_panel"):

        header_left, header_right = st.columns([8, 1], gap="small")

        with header_left:
            st.markdown(
                f"""
                <div class="rag-assistant-header">
                    <img
                        src="{RAG_BOT_AVATAR_DATA_URI}"
                        style="
                            width:52px;
                            height:52px;
                            border-radius:50%;
                            flex-shrink:0;
                            display:block;
                            box-shadow:0 6px 18px rgba(99,102,241,.32);
                            margin-right:10px;
                        "
                    />
                    <div style="flex:1;min-width:0;">
                        <div style="color:#f8fafc;font-size:1.04rem;font-weight:750;line-height:1.25;">
                            AI Meeting Assistant
                        </div>
                        <div style="color:#94a3b8;font-size:.72rem;margin-top:3px;line-height:1.2;">
                            Ask anything about your meetings
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with header_right:
            if st.button(
                "×",
                key="close_rag_assistant",
                help="Close Meeting Assistant",
            ):
                st.session_state["rag_assistant_open"] = False
                st.rerun()

        st.markdown(
            "<div style='border-top:1px solid rgba(148,163,184,.14);margin:8px 0 8px 0;'></div>",
            unsafe_allow_html=True,
        )

        # --------------------------------------------------
        # QUICK QUESTIONS
        # --------------------------------------------------

        if st.session_state["rag_show_quick_questions"]:
            with st.container(key="rag_quick_questions"):
                st.markdown(
                    "<div style='font-size:.9rem;font-weight:700;color:#f8fafc;margin:0 0 8px 0;'>Try asking:</div>",
                    unsafe_allow_html=True,
                )

                quick_questions = [
                    "Summarize my latest meeting",
                    "What were the key decisions?",
                ]

                for index, prompt in enumerate(quick_questions):
                    if st.button(
                        f"→  {prompt}",
                        key=f"rag_quick_question_{index}",
                        use_container_width=True,
                    ):
                        # Suggestions are temporary. The clicked question becomes
                        # the user message and the buttons disappear immediately.
                        st.session_state["rag_show_quick_questions"] = False
                        st.session_state["rag_question_input"] = ""
                        _submit_rag_question(prompt)
                        st.rerun()

                st.markdown(
                    "<div style='border-top:1px solid rgba(148,163,184,.10);margin:8px 0 8px 0;'></div>",
                    unsafe_allow_html=True,
                )

        # --------------------------------------------------
        # INNER CHAT HISTORY
        # --------------------------------------------------

        # This is deliberately the ONLY element with a fixed height.
        # The surrounding panel never scrolls.
        chat_height = 350 if st.session_state["rag_show_quick_questions"] else 420

        with st.container(
            height=chat_height,
            border=False,
            key="rag_chat_history",
        ):
            for message in st.session_state["rag_messages"]:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

                    sources = message.get("sources") or []

                    if sources:
                        with st.expander(
                            f"Sources ({len(sources)})",
                            expanded=False,
                        ):
                            for source in sources:
                                meeting_id = source.get("meeting_id", "Unknown")
                                chunk_index = source.get("chunk_index", "?")
                                score = source.get("score")
                                relevance = (
                                    f" • {float(score):.2f}"
                                    if score is not None
                                    else ""
                                )
                                st.markdown(
                                    f"**Meeting #{meeting_id} • Chunk {chunk_index}{relevance}**"
                                )
                                source_text = str(
                                    source.get("text", "") or ""
                                ).strip()
                                if source_text:
                                    st.caption(source_text)

        # --------------------------------------------------
        # INPUT + SEND
        # --------------------------------------------------

        with st.form(
            "rag_chat_input_form",
            clear_on_submit=True,
        ):
            input_col, send_col = st.columns(
                [8, 1],
                gap="small",
                vertical_alignment="center",
            )

            with input_col:
                question = st.text_input(
                    "Ask about your meetings",
                    value=st.session_state.get(
                        "rag_question_input",
                        "",
                    ),
                    placeholder="Ask about your meetings...",
                    label_visibility="collapsed",
                )

            with send_col:
                submitted = st.form_submit_button(
                    "➤",
                    use_container_width=True,
                )

        if submitted and question.strip():
            st.session_state["rag_question_input"] = ""
            st.session_state["rag_show_quick_questions"] = False
            _submit_rag_question(question.strip())
            st.rerun()

        st.markdown(
            '<div class="rag-assistant-footer">Powered by AI • Uses your meeting transcripts</div>',
            unsafe_allow_html=True,
        )

        if len(st.session_state["rag_messages"]) > 1:
            if st.button(
                "Clear conversation",
                use_container_width=True,
                key="clear_rag_assistant",
            ):
                st.session_state["rag_messages"] = [
                    {
                        "role": "assistant",
                        "content": (
                            "Hi! I'm your AI Meeting Assistant. "
                            "I can help you find information from your meeting transcripts, "
                            "answer questions, and summarize discussions."
                        ),
                        "sources": [],
                    }
                ]
                st.session_state["rag_question_input"] = ""
                st.session_state["rag_show_quick_questions"] = True
                st.rerun()


def _submit_rag_question(question: str) -> None:
    """Send one question to the existing FastAPI RAG endpoint."""

    st.session_state["rag_messages"].append(
        {"role": "user", "content": question, "sources": []}
    )

    try:
        client = APIClient()
        response = client.ask_meetings(question)
        answer = str(
            response.get("answer")
            or response.get("response")
            or "I couldn't find an answer in your meetings."
        ).strip()
        sources = response.get("sources") or []

        st.session_state["rag_messages"].append(
            {
                "role": "assistant",
                "content": answer,
                "sources": sources,
            }
        )

    except requests.HTTPError as exc:
        response = getattr(exc, "response", None)
        detail = "RAG service returned an error."
        if response is not None:
            try:
                payload = response.json()
                detail = payload.get("detail", detail)
            except ValueError:
                pass

        st.session_state["rag_messages"].append(
            {
                "role": "assistant",
                "content": f"I couldn't query your meetings. {detail}",
                "sources": [],
            }
        )

    except Exception as exc:
        st.session_state["rag_messages"].append(
            {
                "role": "assistant",
                "content": f"I couldn't reach the meeting knowledge base. ({exc})",
                "sources": [],
            }
        )

def render_dashboard() -> None:
    """
    Render the complete AI Meeting Intelligence dashboard.
    """

    load_custom_css()

    initialize_dashboard_state()

    # Global floating AI assistant. It does not occupy dashboard layout space.
    render_rag_assistant()

    render_header()

    # ==================================================
    # ACTIVE MEETING
    # ==================================================

    if st.session_state[
        "meeting_active"
    ]:

        st.html(
            """
            <div style="
                text-align:center;
                margin-bottom:0.8rem;
                color:#94a3b8;
                font-size:0.8rem;
            ">
                🎙️ Your meeting is being captured securely
            </div>
            """
        )

        if render_meeting_controls():

            completed = (
                handle_end_meeting()
            )

            if completed:

                st.rerun()

            return

        render_live_recording()

        return

    # ==================================================
    # COMPLETED MEETING
    # ==================================================

    if st.session_state.get(
        "audio_path"
    ):

        if st.button(
            "🔴  Start New Meeting",
            use_container_width=True,
            key="start_new_meeting_button",
        ):

            st.session_state[
                "audio_path"
            ] = None

            st.session_state[
                "transcript"
            ] = None

            st.session_state[
                "word_timestamps"
            ] = []

            st.session_state[
                "speaker_transcript"
            ] = None

            st.session_state[
                "meeting_id"
            ] = None

            st.session_state[
                "meeting_title"
            ] = None

            st.session_state[
                "completed_duration_seconds"
            ] = 0

            st.session_state[
                "meeting_paused"
            ] = False

            st.session_state[
                "active_duration_before_pause"
            ] = 0

            st.session_state[
                "pause_started_at"
            ] = None

            st.session_state[
                "audio_level"
            ] = 0.0

            st.session_state[
                "analysis"
            ] = None

            st.session_state[
                "mom"
            ] = None

            started = (
                handle_start_meeting()
            )

            if started:

                st.rerun()

            return

        render_completed_meeting()

        return

    # ==================================================
    # HISTORICAL MEETING
    # ==================================================

    if st.session_state.get(
        "selected_history_meeting_id"
    ) is not None:

        render_historical_meeting_view()

        return

    # ==================================================
    # LANDING PAGE
    # ==================================================

    render_hero()

    if st.button(
        "🔴  Start Meeting",
        use_container_width=True,
        key="initial_start_meeting_button",
    ):

        started = (
            handle_start_meeting()
        )

        if started:

            st.rerun()

        return

    render_empty_state()

    render_meeting_history()

    st.markdown(
        "<div style='height:1.2rem;'></div>",
        unsafe_allow_html=True,
    )

    render_capability_cards()

    render_footer()
