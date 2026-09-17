from google import genai

from config.settings import settings
from core.exceptions import AIProcessingError


class GeminiEmbeddingProvider:
    """
    Generates vector embeddings using Google's Gemini API.
    """

    def __init__(self) -> None:
        """
        Initialize the Gemini client.
        """

        if not settings.gemini_api_key:
            raise AIProcessingError(
                "GEMINI_API_KEY is not configured."
            )

        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

        self.model = settings.gemini_embedding_model

    def embed_text(self, text: str) -> list[float]:
        """
        Generate an embedding for a single text string.

        Args:
            text: Text to embed.

        Returns:
            list[float]: Embedding vector.

        Raises:
            AIProcessingError: If embedding generation fails.
        """

        if not text or not text.strip():
            raise AIProcessingError(
                "Cannot generate an embedding for empty text."
            )

        try:
            response = self.client.models.embed_content(
                model=self.model,
                contents=text,
            )

            if not response.embeddings:
                raise AIProcessingError(
                    "Gemini returned no embedding."
                )

            values = response.embeddings[0].values

            if not values:
                raise AIProcessingError(
                    "Gemini returned an empty embedding."
                )

            return list(values)

        except AIProcessingError:
            raise

        except Exception as exc:
            raise AIProcessingError(
                "Failed to generate Gemini text embedding."
            ) from exc
