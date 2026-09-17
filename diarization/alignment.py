from dataclasses import dataclass


@dataclass(frozen=True)
class AlignedWord:
    """
    Represents a transcription word assigned to a speaker
    and, when available, a specific diarization segment.
    """

    word: str
    start: float
    end: float
    speaker: str | None
    probability: float | None = None
    diarization_segment_index: int | None = None


@dataclass(frozen=True)
class SpeakerTranscriptSegment:
    """
    Represents a continuous speaker transcript segment.
    """

    speaker: str
    start: float
    end: float
    text: str


class SpeakerTranscriptAligner:
    """
    Aligns Whisper word-level timestamps with
    pyannote speaker diarization segments.
    """

    def __init__(
        self,
        max_gap_seconds: float = 0.5,
    ) -> None:
        if max_gap_seconds < 0:
            raise ValueError(
                "max_gap_seconds cannot be negative."
            )

        self.max_gap_seconds = max_gap_seconds

    @staticmethod
    def _get_segment_start(segment) -> float:
        """
        Support both the Pydantic SpeakerSegment schema
        and the SQLAlchemy SpeakerSegment model.
        """

        if hasattr(segment, "start"):
            return float(segment.start)

        return float(segment.start_time)

    @staticmethod
    def _get_segment_end(segment) -> float:
        """
        Support both the Pydantic SpeakerSegment schema
        and the SQLAlchemy SpeakerSegment model.
        """

        if hasattr(segment, "end"):
            return float(segment.end)

        return float(segment.end_time)

    @staticmethod
    def _clean_word(word: str) -> str:
        """
        Normalize a Whisper word before adding it
        to the speaker transcript.
        """

        return word.strip()

    @staticmethod
    def _join_words(words: list[str]) -> str:
        """
        Reconstruct readable transcript text from
        Whisper word tokens.
        """

        cleaned_words = [
            word.strip()
            for word in words
            if word and word.strip()
        ]

        if not cleaned_words:
            return ""

        text = " ".join(cleaned_words)

        # Remove spaces before punctuation.
        for mark in [
            ",",
            ".",
            "!",
            "?",
            ":",
            ";",
            "%",
        ]:
            text = text.replace(
                f" {mark}",
                mark,
            )

        return text.strip()

    def align_words(
        self,
        words,
        speaker_segments,
    ) -> list[AlignedWord]:
        """
        Assign each Whisper word to the diarization
        segment with the greatest temporal overlap.

        The selected diarization segment index is also
        preserved so that grouping can respect actual
        pyannote boundaries.
        """

        aligned_words: list[AlignedWord] = []

        for word in words:
            word_start = float(word.start)
            word_end = float(word.end)

            best_speaker: str | None = None
            best_segment_index: int | None = None
            best_overlap = 0.0

            for index, segment in enumerate(
                speaker_segments
            ):
                segment_start = (
                    self._get_segment_start(segment)
                )

                segment_end = (
                    self._get_segment_end(segment)
                )

                overlap_start = max(
                    word_start,
                    segment_start,
                )

                overlap_end = min(
                    word_end,
                    segment_end,
                )

                overlap = max(
                    0.0,
                    overlap_end - overlap_start,
                )

                if overlap > best_overlap:
                    best_overlap = overlap
                    best_speaker = str(
                        segment.speaker
                    )
                    best_segment_index = index

            aligned_words.append(
                AlignedWord(
                    word=self._clean_word(
                        word.word
                    ),
                    start=word_start,
                    end=word_end,
                    speaker=best_speaker,
                    probability=getattr(
                        word,
                        "probability",
                        None,
                    ),
                    diarization_segment_index=(
                        best_segment_index
                    ),
                )
            )

        return aligned_words

    def group_by_speaker(
        self,
        aligned_words: list[AlignedWord],
    ) -> list[SpeakerTranscriptSegment]:
        """
        Group words into meaningful speaker turns.

        A new transcript segment is created when:

        1. The speaker changes.
        2. The diarization segment changes and the gap
           between words is greater than max_gap_seconds.
        3. A word has no diarization assignment.

        This preserves actual pyannote boundaries while
        avoiding excessive fragmentation caused by tiny
        diarization gaps.
        """

        if not aligned_words:
            return []

        segments: list[
            SpeakerTranscriptSegment
        ] = []

        first_word = aligned_words[0]

        current_speaker = first_word.speaker
        current_start = first_word.start
        current_end = first_word.end
        current_segment_index = (
            first_word.diarization_segment_index
        )
        current_words = [first_word.word]

        for word in aligned_words[1:]:
            gap = max(
                0.0,
                word.start - current_end,
            )

            same_speaker = (
                word.speaker == current_speaker
            )

            same_diarization_segment = (
                word.diarization_segment_index
                == current_segment_index
            )

            can_merge_different_segments = (
                same_speaker
                and current_speaker is not None
                and word.diarization_segment_index
                is not None
                and current_segment_index
                is not None
                and gap <= self.max_gap_seconds
            )

            should_merge = (
                same_speaker
                and (
                    same_diarization_segment
                    or can_merge_different_segments
                )
            )

            if should_merge:
                current_words.append(word.word)
                current_end = word.end

                if (
                    word.diarization_segment_index
                    != current_segment_index
                ):
                    current_segment_index = (
                        word.diarization_segment_index
                    )

                continue

            text = self._join_words(
                current_words
            )

            if text:
                segments.append(
                    SpeakerTranscriptSegment(
                        speaker=(
                            current_speaker
                            or "UNKNOWN"
                        ),
                        start=current_start,
                        end=current_end,
                        text=text,
                    )
                )

            current_speaker = word.speaker
            current_start = word.start
            current_end = word.end
            current_segment_index = (
                word.diarization_segment_index
            )
            current_words = [word.word]

        text = self._join_words(
            current_words
        )

        if text:
            segments.append(
                SpeakerTranscriptSegment(
                    speaker=(
                        current_speaker
                        or "UNKNOWN"
                    ),
                    start=current_start,
                    end=current_end,
                    text=text,
                )
            )

        return segments
