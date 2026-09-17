
from dataclasses import dataclass
from enum import Enum
import re


class InputCategory(str, Enum):
    GREETING = "greeting"
    CAPABILITY = "capability"
    MEETING_QUERY = "meeting_query"
    OFF_TOPIC = "off_topic"
    PROMPT_INJECTION = "prompt_injection"
    EMPTY = "empty"


@dataclass(frozen=True)
class GuardrailResult:
    allowed: bool
    category: InputCategory
    response: str | None = None


class RAGInputGuardrail:
    """
    Input guardrail for the AI Meeting Intelligence assistant.

    Handles greetings and capability questions directly,
    blocks common prompt-injection attempts, and allows
    natural-language questions about meeting content.
    """

    GREETINGS = {
        "hi",
        "hello",
        "hey",
        "good morning",
        "good afternoon",
        "good evening",
        "how are you",
    }

    CAPABILITY_QUESTIONS = {
        "who are you",
        "what are you",
        "what can you do",
        "how can you help",
        "what is your purpose",
    }

    INJECTION_PATTERNS = (
        r"\bignore\b.{0,50}\b(previous|prior|all)\b.{0,30}\binstructions?\b",
        r"\bignore\b.{0,30}\byour instructions\b",
        r"\breveal\b.{0,30}\bsystem prompt\b",
        r"\bshow\b.{0,30}\bsystem prompt\b",
        r"\bprint\b.{0,30}\bsystem prompt\b",
        r"\bforget\b.{0,30}\b(all rules|your rules|instructions)\b",
        r"\bbypass\b.{0,30}\b(guardrails|safety|instructions)\b",
        r"\b(jailbreak|developer mode)\b",
    )

    MEETING_KEYWORDS = (
        "meeting",
        "transcript",
        "summary",
        "summarize",
        "decision",
        "action item",
        "minutes",
        "discussion",
        "discussed",
        "attendee",
        "speaker",
        "assigned",
        "responsible",
        "deadline",
        "follow-up",
        "follow up",
        "recording",
        "agenda",
        "joined",
        "join the team",
        "who said",
        "what did",
        "what was said",
        "what happened",
        "what was decided",
        "what was discussed",
        "what did we",
        "who mentioned",
        "who worked",
        "experience",
        "mentioned",
        "said about",
        "action",
        "decision",
        "team",
        "project",
    )

    DIRECT_CAPABILITY_RESPONSE = (
        "I'm your AI Meeting Assistant. I can search your recorded "
        "meeting transcripts and answer questions about discussions, "
        "decisions, action items, and summaries."
    )

    OFF_TOPIC_RESPONSE = (
        "I can help with information from your recorded meetings. "
        "Try asking about a meeting, its discussion, decisions, "
        "summary, or action items."
    )

    INJECTION_RESPONSE = (
        "I can't help override my instructions or reveal hidden "
        "system information. I can still help you search your "
        "meeting transcripts."
    )

    def check(self, question: str) -> GuardrailResult:
        if not question or not question.strip():
            return GuardrailResult(
                allowed=False,
                category=InputCategory.EMPTY,
                response="Please enter a question about your meetings.",
            )

        normalized = " ".join(question.lower().strip().split())
        cleaned = normalized.strip(" .!?")

        # Check injection attempts before other categories.
        if any(
            re.search(pattern, normalized)
            for pattern in self.INJECTION_PATTERNS
        ):
            return GuardrailResult(
                allowed=False,
                category=InputCategory.PROMPT_INJECTION,
                response=self.INJECTION_RESPONSE,
            )

        if cleaned in self.GREETINGS:
            return GuardrailResult(
                allowed=False,
                category=InputCategory.GREETING,
                response=self.DIRECT_CAPABILITY_RESPONSE,
            )

        if cleaned in self.CAPABILITY_QUESTIONS:
            return GuardrailResult(
                allowed=False,
                category=InputCategory.CAPABILITY,
                response=self.DIRECT_CAPABILITY_RESPONSE,
            )

        # Allow questions containing known meeting terms.
        if any(
            keyword in normalized
            for keyword in self.MEETING_KEYWORDS
        ):
            return GuardrailResult(
                allowed=True,
                category=InputCategory.MEETING_QUERY,
            )

        # Allow common question forms that may refer to meeting content
        # without explicitly saying "meeting".
        natural_question_patterns = (
    r"^(who|what|when|where|why|how)\b.*\b("
    r"meeting|transcript|discussion|discussed|decision|"
    r"action|agenda|attendee|speaker|team|nico|"
    r"said|mentioned|joined|experience|deadline|"
    r"responsible|assigned|follow.?up|recording|"
    r"worked|contributed|introduced|"
    r"decided|summarize|summarise"
    r")\b",
)

        if any(
            re.search(pattern, normalized)
            for pattern in natural_question_patterns
        ):
            return GuardrailResult(
                allowed=True,
                category=InputCategory.MEETING_QUERY,
            )

        return GuardrailResult(
            allowed=False,
            category=InputCategory.OFF_TOPIC,
            response=self.OFF_TOPIC_RESPONSE,
        )