from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration.

    Values can be loaded from environment variables
    or from the .env file.
    """

    app_name: str = "AI Meeting Intelligence"
    app_version: str = "1.0.0"
    debug: bool = True

    # --------------------------------------------------
    # Database
    # --------------------------------------------------

    database_url: str = ""

    # --------------------------------------------------
    # AI - Groq
    # --------------------------------------------------

    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"

    # --------------------------------------------------
    # AI - Gemini Embeddings
    # --------------------------------------------------

    gemini_api_key: str = Field(
        default="",
        validation_alias="GEMINI_API_KEY",
    )

    gemini_embedding_model: str = "gemini-embedding-001"

    # --------------------------------------------------
    # Vector Database - Qdrant
    # --------------------------------------------------

    qdrant_url: str = Field(
        default="",
        validation_alias="QDRANT_URL",
    )

    qdrant_api_key: str = Field(
        default="",
        validation_alias="QDRANT_API_KEY",
    )

    qdrant_collection: str = "meeting_transcripts"

    # --------------------------------------------------
    # Hugging Face
    # --------------------------------------------------

    huggingface_token: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
