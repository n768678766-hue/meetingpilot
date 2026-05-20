# MeetingPilot Agent Notes

## Project Scope
- MeetingPilot is an internal productivity AI workflow assistant for meeting notes.
- The MVP should stay focused on pasted transcript text, structured minutes, action items, uncertainty flags, exports, and bad-case review.
- Prefer small, behavior-focused changes over broad rewrites.

## Technical Direction
- Frontend: Streamlit.
- LLM access: OpenAI-compatible API, configurable for OpenAI or DeepSeek.
- Storage: local JSON/CSV files under `data/`.
- Exports: Markdown and CSV.

## Working Rules
- Read `README.md`, `architecture.md`, and relevant docs before implementation.
- Keep generated data out of git.
- Do not add unrelated agent frameworks or multi-agent orchestration unless explicitly requested.
- Preserve the MVP boundary: input -> structure -> export -> bad-case learning.

