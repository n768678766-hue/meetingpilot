# MeetingPilot Architecture

## Product Boundary

MeetingPilot is a single-user local MVP for post-transcription meeting text structuring (not an audio transcription product).

The first version should optimize for a clear workflow:

```text
Transcript input (paste or upload .txt / .md / .srt / .vtt)
-> LLM structured extraction
-> Schema validation
-> Human review
-> Markdown/CSV export
-> Bad-case logging
```

## Core Modules

- `app.py`: Streamlit UI and page flow.
- `config.py`: Environment and model settings.
- `llm_client.py`: OpenAI-compatible API calls.
- `prompts.py`: Prompt templates and output instructions.
- `models.py`: Pydantic schemas for meeting notes, action items, uncertainty flags, and bad cases.
- `exporters.py`: Markdown and CSV conversion.
- `storage.py`: Local persistence for outputs and bad-case records.

## Data Flow

1. User pastes transcript text or uploads a transcript file (.txt, .md, .srt, .vtt).
2. UI sends transcript and options to the extraction service.
3. LLM returns JSON matching the expected schema.
4. App validates and displays structured sections.
5. User exports Markdown/CSV or records a bad case.

## MVP Non-Goals

- Audio recording and transcription (ASR).
- Calendar integration.
- Enterprise authentication.
- Multi-agent orchestration.
- Team collaboration features.

