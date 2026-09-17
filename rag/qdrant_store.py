from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)

from config.settings import settings


class QdrantStore:
    """
    Handles Qdrant connection, collection management,
    payload indexing, and semantic vector search
    for the AI Meeting Intelligence RAG system.
    """

    VECTOR_SIZE = 3072

    def __init__(self) -> None:
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
        )

        self.collection_name = settings.qdrant_collection

    def collection_exists(self) -> bool:
        """
        Check whether the meeting transcript collection exists.
        """

        collections = self.client.get_collections()

        return any(
            collection.name == self.collection_name
            for collection in collections.collections
        )

    def create_collection(self) -> None:
        """
        Create the meeting transcript collection
        if it does not already exist.
        """

        if self.collection_exists():
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )

    def create_payload_indexes(self) -> None:
        """
        Create indexes required for filtered search.
        """

        collection_info = self.get_collection_info()

        payload_schema = (
            collection_info.payload_schema or {}
        )

        if "meeting_id" in payload_schema:
            return

        self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="meeting_id",
            field_schema=PayloadSchemaType.INTEGER,
        )

    def ensure_collection(self) -> None:
        """
        Ensure that the collection and required
        payload indexes exist.
        """

        self.create_collection()
        self.create_payload_indexes()

    def get_collection_info(self):
        """
        Return information about the meeting transcript collection.
        """

        return self.client.get_collection(
            collection_name=self.collection_name
        )

    def search(
        self,
        query_vector: list[float],
        limit: int = 5,
        meeting_id: int | None = None,
    ) -> list:
        """
        Search the meeting transcript collection
        using vector similarity.

        This method performs retrieval only.
        Collection initialization is handled separately.
        """

        query_filter = None

        if meeting_id is not None:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="meeting_id",
                        match=MatchValue(
                            value=meeting_id
                        ),
                    )
                ]
            )

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )

        return results.points

    def upsert_points(
        self,
        points: list[PointStruct],
    ) -> None:
        """
        Insert or update vector points in Qdrant.
        """

        if not points:
            return

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )
