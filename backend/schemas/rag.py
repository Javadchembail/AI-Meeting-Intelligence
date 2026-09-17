from pydantic import BaseModel, Field


class RAGQuestionRequest(BaseModel):
    """
    Request body for asking a question about meetings.
    """

    question: str = Field(
        ...,
        min_length=1,
        description="Question to ask about meeting transcripts.",
    )

    meeting_id: int | None = Field(
        default=None,
        description=(
            "Optional meeting ID. "
            "If omitted, search across all indexed meetings."
        ),
    )

    limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of transcript chunks to retrieve.",
    )


class RAGSource(BaseModel):
    """
    Source transcript chunk used to generate the answer.
    """

    meeting_id: int
    chunk_index: int
    text: str
    score: float


class RAGQuestionResponse(BaseModel):
    """
    Response returned by the meeting RAG endpoint.
    """

    question: str
    answer: str
    sources: list[RAGSource] = Field(
        default_factory=list,
    )
