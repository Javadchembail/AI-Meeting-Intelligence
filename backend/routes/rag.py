
import re

import logfire
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.session import get_database_session
from backend.repositories.meeting_repository import MeetingRepository
from backend.schemas.rag import (
    RAGQuestionRequest,
    RAGQuestionResponse,
    RAGSource,
)
from core.exceptions import AIProcessingError
from core.logging import logger
from guardrails.input_guardrail import RAGInputGuardrail
from rag.rag_service import RAGService


router = APIRouter(
    prefix="/rag",
    tags=["RAG"],
)

input_guardrail = RAGInputGuardrail()


def resolve_meeting_id(
    question: str,
    requested_meeting_id: int | None,
    repository: MeetingRepository,
) -> tuple[int | None, str | None]:
    """Resolve explicit meeting references or latest-meeting requests."""

    if requested_meeting_id is not None:
        meeting = repository.get_by_id(requested_meeting_id)

        if meeting is None:
            return None, (
                f"Meeting {requested_meeting_id} was not found."
            )

        return requested_meeting_id, None

    normalized = question.lower()

    match = re.search(
        r"\bmeeting\s*#?\s*(\d+)\b",
        normalized,
    )

    if match:
        meeting_id = int(match.group(1))
        meeting = repository.get_by_id(meeting_id)

        if meeting is None:
            return None, f"Meeting {meeting_id} was not found."

        return meeting_id, None

    latest_phrases = (
        "latest meeting",
        "most recent meeting",
        "last meeting",
    )

    if any(phrase in normalized for phrase in latest_phrases):
        meeting = repository.get_latest()

        if meeting is None:
            return None, "There are no meetings in the database yet."

        return meeting.id, None

    return None, None


@router.post(
    "/ask",
    response_model=RAGQuestionResponse,
    status_code=status.HTTP_200_OK,
)
def ask_meetings(
    request: RAGQuestionRequest,
    db: Session = Depends(get_database_session),
) -> RAGQuestionResponse:
    """Answer meeting questions after checking input guardrails."""

    with logfire.span(
        "rag.ask",
        requested_meeting_id=request.meeting_id,
        question_length=len(request.question),
        limit=request.limit,
    ) as span:
        try:
            # --------------------------------------------------
            # 1. Input guardrail
            # --------------------------------------------------
            with logfire.span("rag.input_guardrail"):
                guardrail_result = input_guardrail.check(
                    request.question
                )

            logger.info(
                "RAG input guardrail category=%s allowed=%s",
                guardrail_result.category.value,
                guardrail_result.allowed,
            )

            span.set_attribute(
                "rag.guardrail.category",
                guardrail_result.category.value,
            )
            span.set_attribute(
                "rag.guardrail.allowed",
                guardrail_result.allowed,
            )

            if not guardrail_result.allowed:
                span.set_attribute("rag.status", "blocked")

                return RAGQuestionResponse(
                    question=request.question,
                    answer=(
                        guardrail_result.response
                        or "Please ask a question about your meetings."
                    ),
                    sources=[],
                )

            # --------------------------------------------------
            # 2. Resolve meeting ID
            # --------------------------------------------------
            repository = MeetingRepository(db)

            with logfire.span("rag.resolve_meeting"):
                meeting_id, resolution_error = resolve_meeting_id(
                    question=request.question,
                    requested_meeting_id=request.meeting_id,
                    repository=repository,
                )

            span.set_attribute(
                "rag.resolved_meeting_id",
                meeting_id,
            )

            if resolution_error:
                span.set_attribute(
                    "rag.status",
                    "meeting_resolution_error",
                )

                return RAGQuestionResponse(
                    question=request.question,
                    answer=resolution_error,
                    sources=[],
                )

            # --------------------------------------------------
            # 3. Execute RAG service
            # --------------------------------------------------
            service = RAGService()

            with logfire.span(
                "rag.service.ask",
                meeting_id=meeting_id,
                limit=request.limit,
            ):
                result = service.ask(
                    question=request.question,
                    meeting_id=meeting_id,
                    limit=request.limit,
                )

            # --------------------------------------------------
            # 4. Log answer at route boundary
            # --------------------------------------------------
            logger.info(
                "RAG answer at route boundary: %r",
                result.answer,
            )

            # --------------------------------------------------
            # 5. Build API response
            # --------------------------------------------------
            response = RAGQuestionResponse(
                question=result.question,
                answer=result.answer,
                sources=[
                    RAGSource(
                        meeting_id=source.meeting_id,
                        chunk_index=source.chunk_index,
                        text=source.text,
                        score=source.score,
                    )
                    for source in result.sources
                ],
            )

            logger.info(
                "RAG answer in response model: %r",
                response.answer,
            )

            # --------------------------------------------------
            # 6. Log successful completion
            # --------------------------------------------------
            span.set_attribute(
                "rag.sources_count",
                len(response.sources),
            )
            span.set_attribute(
                "rag.status",
                "success",
            )

            logfire.info(
                "RAG question answered",
                meeting_id=meeting_id,
                sources_count=len(response.sources),
            )

            return response

        except AIProcessingError as exc:
            span.set_attribute(
                "rag.status",
                "ai_processing_error",
            )

            logfire.warning(
                "RAG processing error",
                error=str(exc),
            )

            logger.warning(
                "RAG processing error: %s",
                str(exc),
            )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        except Exception as exc:
            span.set_attribute(
                "rag.status",
                "error",
            )

            logfire.error(
                "Unable to answer the meeting question",
                error=str(exc),
            )

            logger.exception(
                "Unable to answer the meeting question."
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to answer the meeting question.",
            ) from exc