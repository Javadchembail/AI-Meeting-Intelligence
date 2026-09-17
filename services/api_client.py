import requests


class APIClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
    ) -> None:
        self.base_url = base_url.rstrip("/")

    # ==================================================
    # HEALTH
    # ==================================================

    def health_check(self) -> dict:
        response = requests.get(
            f"{self.base_url}/",
            timeout=10,
        )

        response.raise_for_status()

        return response.json()

    # ==================================================
    # MEETINGS
    # ==================================================

    def start_meeting(
        self,
        title: str,
    ) -> dict:

        response = requests.post(
            f"{self.base_url}/meetings",
            json={
                "title": title,
            },
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    def get_all_meetings(self) -> list[dict]:

        response = requests.get(
            f"{self.base_url}/meetings",
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    def get_meeting(
        self,
        meeting_id: int,
    ) -> dict:

        response = requests.get(
            f"{self.base_url}/meetings/{meeting_id}",
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    # ==================================================
    # AUDIO
    # ==================================================

    def get_audio_level(
        self,
        meeting_id: int,
    ) -> float:

        response = requests.get(
            f"{self.base_url}/meetings/"
            f"{meeting_id}/audio-level",
            timeout=5,
        )

        response.raise_for_status()

        data = response.json()

        level = float(
            data.get(
                "level",
                0.0,
            )
        )

        return max(
            0.0,
            min(
                1.0,
                level,
            ),
        )

    # ==================================================
    # MEETING CONTROLS
    # ==================================================

    def pause_meeting(
        self,
        meeting_id: int,
    ) -> dict:

        response = requests.post(
            f"{self.base_url}/meetings/"
            f"{meeting_id}/pause",
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    def resume_meeting(
        self,
        meeting_id: int,
    ) -> dict:

        response = requests.post(
            f"{self.base_url}/meetings/"
            f"{meeting_id}/resume",
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    def end_meeting(
        self,
        meeting_id: int,
    ) -> dict:

        response = requests.post(
            f"{self.base_url}/meetings/"
            f"{meeting_id}/end",
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    def delete_meeting(
        self,
        meeting_id: int,
    ) -> None:

        response = requests.delete(
            f"{self.base_url}/meetings/{meeting_id}",
            timeout=30,
        )

        response.raise_for_status()

    # ==================================================
    # TRANSCRIPTION
    # ==================================================

    def transcribe_meeting(
        self,
        meeting_id: int,
    ) -> dict:

        response = requests.post(
            f"{self.base_url}/meetings/"
            f"{meeting_id}/transcribe",
            timeout=300,
        )

        response.raise_for_status()

        return response.json()

    def get_meeting_transcript(
        self,
        meeting_id: int,
    ) -> dict:

        response = requests.get(
            f"{self.base_url}/meetings/"
            f"{meeting_id}/transcript",
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    # ==================================================
    # SPEAKER TRANSCRIPT
    # ==================================================

    def get_speaker_transcript(
        self,
        meeting_id: int,
    ) -> dict:

        response = requests.get(
            f"{self.base_url}/meetings/"
            f"{meeting_id}/speaker-transcript",
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    # ==================================================
    # AI ANALYSIS
    # ==================================================

    def analyze_meeting(
        self,
        meeting_id: int,
    ) -> dict:

        response = requests.post(
            f"{self.base_url}/meetings/"
            f"{meeting_id}/analyze",
            timeout=300,
        )

        response.raise_for_status()

        return response.json()

    def get_meeting_analysis(
        self,
        meeting_id: int,
    ) -> dict:

        response = requests.get(
            f"{self.base_url}/meetings/"
            f"{meeting_id}/analysis",
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    # ==================================================
    # MINUTES OF MEETING
    # ==================================================

    def generate_mom(
        self,
        meeting_id: int,
    ) -> dict:

        response = requests.post(
            f"{self.base_url}/meetings/"
            f"{meeting_id}/mom",
            timeout=300,
        )

        response.raise_for_status()

        return response.json()

    # ==================================================
    # DIARIZATION
    # ==================================================

    def diarize_meeting(
        self,
        meeting_id: int,
    ) -> dict:

        response = requests.post(
            f"{self.base_url}/meetings/"
            f"{meeting_id}/diarize",
            timeout=600,
        )

        response.raise_for_status()

        return response.json()

    def get_meeting_diarization(
        self,
        meeting_id: int,
    ) -> dict:

        response = requests.get(
            f"{self.base_url}/meetings/"
            f"{meeting_id}/diarization",
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    # ==================================================
    # RAG — ASK MY MEETINGS
    # ==================================================

    def ask_meetings(
        self,
        question: str,
    ) -> dict:

        if not question or not question.strip():
            raise ValueError(
                "Question cannot be empty."
            )

        response = requests.post(
            f"{self.base_url}/rag/ask",
            json={
                "question": question.strip(),
            },
            timeout=120,
        )

        response.raise_for_status()

        return response.json()