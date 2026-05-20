# API Notes

The MVP uses an OpenAI-compatible chat completions API.

Configuration keys:

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`

DeepSeek can be used by setting a compatible base URL and model name.

Example `.env` for OpenAI:

```text
OPENAI_API_KEY=<your-openai-api-key>
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
```

Example `.env` for a DeepSeek-compatible endpoint:

```text
OPENAI_API_KEY=<your-deepseek-api-key>
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-v4-pro
```

If no API key is present, the Streamlit app calls the deterministic fallback extractor in `llm_client.py`. This keeps demos, screenshots, export checks, and bad-case logging available offline.

The LLM response is parsed as JSON and validated against the `MeetingResult` Pydantic schema before display or storage.
