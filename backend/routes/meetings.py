import logfire

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from backend.database.session import (
    get_database_session,
)
from backend.repositories.speaker_segment_repository import (
    SpeakerSegmentRepository,
)
from backend.schemas.diarization import (
    DiarizationResponse,
    SpeakerSegmentResponse,
)
from backend.schemas.meeting import (
    MeetingCreate,
    MeetingResponse,
)
from backend.schemas.meeting_analysis import (
    MeetingAnalysisResponse,
)
from backend.schemas.mom import (
    MinutesOfMeeting,
)
from backend.schemas.speaker_transcript import (
    SpeakerTranscriptResponse,
    SpeakerTranscriptSegmentResponse,
)
from backend.schemas.transcript import (
    TranscriptResponse,
)
from backend.services.diarization_service import (
    MeetingDiarizationService,
)
from backend.services.meeting_analysis_service import (
    MeetingAnalysisService,
)
from backend.services.meeting_service import (
    MeetingService,
)
from backend.services.mom_service import (
    MoMService,
)
from backend.services.speaker_transcript_service import (
    SpeakerTranscriptService,
)
from backend.services.transcript_service import (
    TranscriptService,
)
from core.exceptions import AudioProcessingError
from diarization.pyannote_provider import (
    PyannoteDiarizationProvider,
)
from diarization.service import (
    DiarizationService,
)


router = APIRouter(
    prefix="/meetings",
    tags=["Meetings"],
)


# ==================================================
# CREATE MEETING
# ==================================================

@router.post(
    "",
    response_model=MeetingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_meeting(
    meeting_data: MeetingCreate,
    session: Session = Depends(
        get_database_session
    ),
) -> MeetingResponse:

    service = MeetingService(
        session
    )

    try:

        meeting = service.start_meeting(
            title=meeting_data.title
        )

        return MeetingResponse.model_validate(
            meeting
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# ==================================================
# GET ALL MEETINGS
# ==================================================

@router.get(
    "",
    response_model=list[MeetingResponse],
    status_code=status.HTTP_200_OK,
)
def get_all_meetings(
    session: Session = Depends(
        get_database_session
    ),
) -> list[MeetingResponse]:

    service = MeetingService(
        session
    )

    meetings = (
        service.get_all_meetings()
    )

    return [
        MeetingResponse.model_validate(
            meeting
        )
        for meeting in meetings
    ]


# ==================================================
# GET SINGLE MEETING
# ==================================================

@router.get(
    "/{meeting_id}",
    response_model=MeetingResponse,
    status_code=status.HTTP_200_OK,
)
def get_meeting(
    meeting_id: int,
    session: Session = Depends(
        get_database_session
    ),
) -> MeetingResponse:

    service = MeetingService(
        session
    )

    meeting = service.get_meeting(
        meeting_id=meeting_id
    )

    if meeting is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Meeting with ID {meeting_id} "
                "was not found."
            ),
        )

    return MeetingResponse.model_validate(
        meeting
    )


# ==================================================
# GET LIVE AUDIO LEVEL
# ==================================================

@router.get(
    "/{meeting_id}/audio-level",
    status_code=status.HTTP_200_OK,
)
def get_audio_level(
    meeting_id: int,
    session: Session = Depends(
        get_database_session
    ),
) -> dict[str, float]:

    """
    Return the current microphone audio level.

    The value is generated directly from the
    active AudioRecorder.

    The level is normalized between 0.0 and 1.0.

    Streamlit can poll this endpoint while a meeting
    is recording and use the value to control the
    height of the live waveform.
    """

    service = MeetingService(
        session
    )

    try:

        level = service.get_audio_level(
            meeting_id=meeting_id
        )

        level = max(
            0.0,
            min(
                1.0,
                float(level),
            ),
        )

        return {
            "level": level
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# ==================================================
# PAUSE MEETING
# ==================================================

@router.post(
    "/{meeting_id}/pause",
    response_model=MeetingResponse,
    status_code=status.HTTP_200_OK,
)
def pause_meeting(
    meeting_id: int,
    session: Session = Depends(
        get_database_session
    ),
) -> MeetingResponse:

    service = MeetingService(
        session
    )

    try:

        meeting = service.pause_meeting(
            meeting_id=meeting_id
        )

        return MeetingResponse.model_validate(
            meeting
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# ==================================================
# RESUME MEETING
# ==================================================

@router.post(
    "/{meeting_id}/resume",
    response_model=MeetingResponse,
    status_code=status.HTTP_200_OK,
)
def resume_meeting(
    meeting_id: int,
    session: Session = Depends(
        get_database_session
    ),
) -> MeetingResponse:

    service = MeetingService(
        session
    )

    try:

        meeting = service.resume_meeting(
            meeting_id=meeting_id
        )

        return MeetingResponse.model_validate(
            meeting
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# ==================================================
# END MEETING
# ==================================================

@router.post(
    "/{meeting_id}/end",
    response_model=MeetingResponse,
    status_code=status.HTTP_200_OK,
)
def end_meeting(
    meeting_id: int,
    session: Session = Depends(
        get_database_session
    ),
) -> MeetingResponse:
    service = MeetingService(session)

    with logfire.span(
        "meeting.end",
        meeting_id=meeting_id,
    ):
        try:
            meeting = service.end_meeting(
                meeting_id=meeting_id
            )

            logfire.info(
                "Meeting ended and audio saved",
                meeting_id=meeting_id,
            )

            return MeetingResponse.model_validate(
                meeting
            )

        except ValueError as exc:
            logfire.warning(
                "Unable to end meeting",
                meeting_id=meeting_id,
                error=str(exc),
            )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc


# ==================================================
# TRANSCRIBE MEETING
# ==================================================

@router.post(
    "/{meeting_id}/transcribe",
    response_model=TranscriptResponse,
    status_code=status.HTTP_200_OK,
)
def transcribe_meeting(
    meeting_id: int,
    session: Session = Depends(
        get_database_session
    ),
) -> TranscriptResponse:

    service = TranscriptService(
        session=session
    )

    try:

        transcript = (
            service.transcribe_meeting(
                meeting_id
            )
        )

        return TranscriptResponse.model_validate(
            transcript
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Unable to transcribe "
                "meeting audio."
            ),
        ) from exc


# ==================================================
# GET MEETING TRANSCRIPT
# ==================================================

@router.get(
    "/{meeting_id}/transcript",
    response_model=TranscriptResponse,
    status_code=status.HTTP_200_OK,
)
def get_meeting_transcript(
    meeting_id: int,
    session: Session = Depends(
        get_database_session
    ),
) -> TranscriptResponse:

    service = TranscriptService(
        session=session
    )

    transcript = (
        service.get_meeting_transcript(
            meeting_id
        )
    )

    if transcript is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Transcript for meeting "
                f"{meeting_id} was not found."
            ),
        )

    return TranscriptResponse.model_validate(
        transcript
    )


# ==================================================
# GET SPEAKER-AWARE TRANSCRIPT
# ==================================================

@router.get(
    "/{meeting_id}/speaker-transcript",
    response_model=SpeakerTranscriptResponse,
    status_code=status.HTTP_200_OK,
)
def get_speaker_transcript(
    meeting_id: int,
    session: Session = Depends(
        get_database_session
    ),
) -> SpeakerTranscriptResponse:

    """
    Return a speaker-aware transcript generated by
    aligning Whisper word timestamps with persisted
    pyannote speaker diarization segments.

    The meeting must already have:

    1. A stored Whisper transcript.
    2. Persisted speaker diarization results.
    """

    service = SpeakerTranscriptService(
        session=session
    )

    try:

        (
            speakers,
            duration_seconds,
            segments,
        ) = service.get_speaker_transcript(
            meeting_id=meeting_id
        )

        return SpeakerTranscriptResponse(
            meeting_id=meeting_id,
            speakers=speakers,
            duration_seconds=duration_seconds,
            segments=[
                SpeakerTranscriptSegmentResponse(
                    speaker=segment.speaker,
                    start=segment.start,
                    end=segment.end,
                    text=segment.text,
                )
                for segment in segments
            ],
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except AudioProcessingError as exc:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Unable to generate "
                "speaker-aware transcript."
            ),
        ) from exc


# ==================================================
# ANALYZE MEETING
# ==================================================

@router.post(
    "/{meeting_id}/analyze",
    response_model=MeetingAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
def analyze_meeting(
    meeting_id: int,
    session: Session = Depends(
        get_database_session
    ),
) -> MeetingAnalysisResponse:

    service = MeetingAnalysisService(
        session=session
    )

    try:

        analysis = (
            service.analyze_meeting(
                meeting_id=meeting_id
            )
        )

        return MeetingAnalysisResponse.model_validate(
            analysis
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Unable to analyze "
                "meeting transcript."
            ),
        ) from exc


# ==================================================
# GET MEETING ANALYSIS
# ==================================================

@router.get(
    "/{meeting_id}/analysis",
    response_model=MeetingAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
def get_meeting_analysis(
    meeting_id: int,
    session: Session = Depends(
        get_database_session
    ),
) -> MeetingAnalysisResponse:

    service = MeetingAnalysisService(
        session=session
    )

    analysis = (
        service.get_meeting_analysis(
            meeting_id=meeting_id
        )
    )

    if analysis is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Analysis for meeting "
                f"{meeting_id} was not found."
            ),
        )

    return MeetingAnalysisResponse.model_validate(
        analysis
    )


# ==================================================
# GENERATE MINUTES OF MEETING
# ==================================================

@router.post(
    "/{meeting_id}/mom",
    response_model=MinutesOfMeeting,
    status_code=status.HTTP_200_OK,
)
def generate_mom(
    meeting_id: int,
    session: Session = Depends(
        get_database_session
    ),
) -> MinutesOfMeeting:

    service = MoMService(
        session=session
    )

    try:

        mom = service.generate_mom(
            meeting_id=meeting_id
        )

        return mom

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Unable to generate "
                "Minutes of Meeting."
            ),
        ) from exc


# ==================================================
# DIARIZE MEETING
# ==================================================

@router.post(
    "/{meeting_id}/diarize",
    response_model=DiarizationResponse,
    status_code=status.HTTP_200_OK,
)
def diarize_meeting(
    meeting_id: int,
    session: Session = Depends(
        get_database_session
    ),
) -> DiarizationResponse:

    """
    Run speaker diarization for a meeting.

    The meeting must have a completed audio recording.
    Detected speaker segments are persisted in PostgreSQL.
    """

    meeting_service = MeetingService(
        session
    )

    meeting = meeting_service.get_meeting(
        meeting_id=meeting_id
    )

    if meeting is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Meeting with ID {meeting_id} "
                "was not found."
            ),
        )

    if not meeting.audio_path:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Meeting does not have an "
                "audio recording."
            ),
        )

    provider = PyannoteDiarizationProvider()

    diarization_service = DiarizationService(
        provider=provider
    )

    service = MeetingDiarizationService(
        session=session,
        diarization_service=diarization_service,
    )

    try:

        result = service.diarize_meeting(
            meeting_id=meeting_id,
            audio_path=meeting.audio_path,
        )

        return DiarizationResponse(
            meeting_id=meeting_id,
            speakers=result.speakers,
            duration_seconds=result.duration_seconds,
            segments=[
                SpeakerSegmentResponse(
                    speaker=segment.speaker,
                    start=segment.start,
                    end=segment.end,
                )
                for segment in result.segments
            ],
        )

    except AudioProcessingError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Unable to diarize "
                "meeting audio."
            ),
        ) from exc


# ==================================================
# GET MEETING DIARIZATION
# ==================================================

@router.get(
    "/{meeting_id}/diarization",
    response_model=DiarizationResponse,
    status_code=status.HTTP_200_OK,
)
def get_meeting_diarization(
    meeting_id: int,
    session: Session = Depends(
        get_database_session
    ),
) -> DiarizationResponse:

    """
    Return persisted speaker diarization results
    for a meeting.
    """

    meeting_service = MeetingService(
        session
    )

    meeting = meeting_service.get_meeting(
        meeting_id=meeting_id
    )

    if meeting is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Meeting with ID {meeting_id} "
                "was not found."
            ),
        )

    repository = SpeakerSegmentRepository(
        session
    )

    segments = repository.get_by_meeting_id(
        meeting_id=meeting_id
    )

    if not segments:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Diarization results for meeting "
                f"{meeting_id} were not found."
            ),
        )

    speakers = sorted(
        {
            segment.speaker
            for segment in segments
        }
    )

    duration_seconds = max(
        segment.end_time
        for segment in segments
    )

    return DiarizationResponse(
        meeting_id=meeting_id,
        speakers=speakers,
        duration_seconds=duration_seconds,
        segments=[
            SpeakerSegmentResponse(
                speaker=segment.speaker,
                start=segment.start_time,
                end=segment.end_time,
            )
            for segment in segments
        ],
    )


# ==================================================
# DELETE MEETING
# ==================================================

@router.delete(
    "/{meeting_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_meeting(
    meeting_id: int,
    session: Session = Depends(
        get_database_session
    ),
) -> None:

    service = MeetingService(
        session
    )

    try:

        service.delete_meeting(
            meeting_id=meeting_id
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
