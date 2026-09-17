from groq import Groq

from ai.schemas import MeetingAnalysis
from config.settings import settings
from core.exceptions import AIProcessingError
from core.logging import logger


class AIAnalysisService:
    """
    Service responsible for analyzing meeting transcripts
    using a Groq-hosted LLM.
    """

    def __init__(
        self,
        client: Groq | None = None,
    ) -> None:

        if client is not None:

            self.client = client

        else:

            if not settings.groq_api_key:

                raise AIProcessingError(
                    "GROQ_API_KEY is not configured."
                )

            self.client = Groq(
                api_key=settings.groq_api_key
            )

        self.model = settings.groq_model

    def analyze_transcript(
        self,
        transcript: str,
    ) -> MeetingAnalysis:
        """
        Analyze a meeting transcript and return
        structured meeting intelligence.
        """

        if not transcript.strip():

            raise AIProcessingError(
                "Cannot analyze an empty transcript."
            )

        prompt = f"""
You are an AI meeting intelligence assistant.

Analyze the following meeting transcript and return
the result as valid JSON.

The JSON must contain these fields:

1. summary
2. key_points
3. decisions
4. action_items
5. next_steps

Each action item must contain:

- task
- assignee
- deadline
- priority

Priority must be one of:

- low
- medium
- high

Important rules:

- Return ONLY valid JSON.
- Do not use Markdown.
- Do not add explanations outside the JSON.
- Do not invent facts.
- Do not invent people or assignees.
- Do not invent deadlines.
- If an assignee is not mentioned, use null.
- If a deadline is not mentioned, use null.
- Only include decisions explicitly supported
  by the transcript.
- Keep the summary concise.
- Keep key points factual.
- Keep next steps grounded in the transcript.

Meeting transcript:

{transcript}
"""

        try:

            logger.info(
                "Starting AI analysis using model: %s",
                self.model,
            )

            completion = (
                self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a precise "
                                "meeting analysis assistant. "
                                "Return only valid JSON."
                            ),
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    temperature=0.2,
                    response_format={
                        "type": "json_object"
                    },
                )
            )

            content = (
                completion
                .choices[0]
                .message
                .content
            )

            if not content:

                raise AIProcessingError(
                    "AI returned an empty response."
                )

            analysis = (
                MeetingAnalysis
                .model_validate_json(
                    content
                )
            )

            logger.info(
                "AI meeting analysis completed "
                "successfully."
            )

            return analysis

        except AIProcessingError:

            raise

        except Exception as exc:

            logger.exception(
                "AI meeting analysis failed."
            )

            raise AIProcessingError(
                "Unable to analyze meeting transcript."
            ) from exc