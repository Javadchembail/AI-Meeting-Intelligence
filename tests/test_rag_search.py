from rag.embeddings import GeminiEmbeddingProvider
from rag.qdrant_store import QdrantStore


def main() -> None:
    query = "What was discussed about Nico?"

    embedding_provider = GeminiEmbeddingProvider()
    qdrant_store = QdrantStore()

    vector = embedding_provider.embed_text(query)

    results = qdrant_store.search(
        vector,
        limit=3,
        meeting_id=36,
    )

    print("Query:", query)
    print("Results:", len(results))

    for result in results:
        payload = result.payload or {}

        print()
        print(f"Score: {result.score:.4f}")
        print(f"Meeting: {payload.get('meeting_id')}")
        print(f"Chunk: {payload.get('chunk_index')}")
        print(f"Text: {payload.get('text')}")

    print()
    print("Semantic search: OK")


if __name__ == "__main__":
    main()
