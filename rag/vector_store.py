from uuid import uuid5, NAMESPACE_URL

from qdrant_client.models import PointStruct

from rag.chunker import TextChunk
from rag.embeddings import GeminiEmbeddingProvider
from rag.qdrant_store import QdrantStore


class TranscriptVectorStore:
    """
    Stores meeting transcript chunks and their embeddings
    in Qdrant.
    """

    def __init__(
        self,
        qdrant_store: QdrantStore | None = None,
        embedding_provider: GeminiEmbeddingProvider | None = None,
    ) -> None:
        self.qdrant_store = (
            qdrant_store
            if qdrant_store is not None
            else QdrantStore()
        )

        self.embedding_provider = (
            embedding_provider
            if embedding_provider is not None
            else GeminiEmbeddingProvider()
        )

        self.qdrant_store.ensure_collection()

    def _create_point_id(
        self,
        meeting_id: int,
        chunk_index: int,
    ) -> str:
        """
        Create a deterministic UUID for a transcript chunk.
        """

        value = (
            f"meeting:{meeting_id}:"
            f"chunk:{chunk_index}"
        )

        return str(
            uuid5(
                NAMESPACE_URL,
                value,
            )
        )

    def index_chunks(
        self,
        meeting_id: int,
        chunks: list[TextChunk],
    ) -> int:
        """
        Generate embeddings for transcript chunks
        and store them in Qdrant.

        Args:
            meeting_id: Meeting database ID.
            chunks: Transcript chunks.

        Returns:
            Number of chunks stored.
        """

        if not chunks:
            return 0

        points: list[PointStruct] = []

        for chunk in chunks:
            vector = self.embedding_provider.embed_text(
                chunk.text
            )

            point = PointStruct(
                id=self._create_point_id(
                    meeting_id=meeting_id,
                    chunk_index=chunk.chunk_index,
                ),
                vector=vector,
                payload={
                    "meeting_id": meeting_id,
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                },
            )

            points.append(point)

        self.qdrant_store.client.upsert(
            collection_name=self.qdrant_store.collection_name,
            points=points,
        )

        return len(points)
