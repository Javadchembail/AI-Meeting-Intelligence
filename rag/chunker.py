from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    """
    Represents a chunk of meeting transcript text.
    """

    text: str
    chunk_index: int


class TranscriptChunker:
    """
    Splits meeting transcripts into overlapping text chunks.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError(
                "chunk_size must be greater than zero."
            )

        if chunk_overlap < 0:
            raise ValueError(
                "chunk_overlap cannot be negative."
            )

        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size."
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, text: str) -> list[TextChunk]:
        """
        Split transcript text into overlapping chunks.

        Args:
            text: Full meeting transcript.

        Returns:
            List of TextChunk objects.
        """

        if not text or not text.strip():
            return []

        normalized_text = " ".join(
            text.split()
        )

        chunks: list[TextChunk] = []

        start = 0
        chunk_index = 0

        while start < len(normalized_text):
            end = min(
                start + self.chunk_size,
                len(normalized_text),
            )

            chunk_text = normalized_text[start:end].strip()

            if chunk_text:
                chunks.append(
                    TextChunk(
                        text=chunk_text,
                        chunk_index=chunk_index,
                    )
                )

                chunk_index += 1

            if end >= len(normalized_text):
                break

            start = end - self.chunk_overlap

        return chunks
