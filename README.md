# AI Meeting Intelligence

AI Meeting Intelligence records meetings, transcribes audio, identifies speakers,
creates summaries and minutes of meeting (MoM), and provides grounded search over
past meeting transcripts.

## Components

- **Streamlit** dashboard for meeting control, history, exports, and RAG chat.
- **FastAPI** backend for meetings, transcription, analysis, diarization, MoM,
  exports, and retrieval endpoints.
- **PostgreSQL** for meeting metadata, transcripts, and analysis.
- **Qdrant** for transcript embeddings and semantic search.
- **Groq** for analysis and grounded RAG answers; **Gemini** for embeddings.

## Prerequisites

- Python 3.11
- PostgreSQL
- Qdrant instance
- Groq and Gemini API keys
- A Hugging Face token authorized for the configured pyannote diarization model
  (only if speaker diarization is used)
- PortAudio and FFmpeg installed on the host for local microphone capture and
  transcription

## Local setup

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set the values in `.env`; it is intentionally excluded from Git. Create database
tables once:

```powershell
python -m backend.database.init_db
```

Start the API:

```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal, start the dashboard:

```powershell
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

Open `http://127.0.0.1:8501`. API health is available at
`http://127.0.0.1:8000/` and interactive API documentation at
`http://127.0.0.1:8000/docs`.

## Important hosting note

The current recorder opens a microphone on the **FastAPI host** using
`sounddevice`. That works for local development but cannot capture a visitor's
microphone when deployed to Render or another cloud host. A production deployment
must replace it with browser-side recording/upload before exposing the Start
Meeting workflow publicly. PostgreSQL, Qdrant, and audio/export storage must also
be provisioned as persistent managed services rather than container-local files.

## Repository hygiene

Secrets, local virtual environments, recordings, generated exports, local test
audio, UI backups, and temporary RAG payloads are excluded by `.gitignore` and
`.dockerignore`. Only source code, configuration templates, tests, and deployment
configuration should be committed.
