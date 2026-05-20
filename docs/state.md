# State Notes

The MVP can keep state local and simple.

Streamlit session state should hold:

- Current transcript input.
- Latest structured meeting result.
- Export preview.
- Bad-case draft.
- API client availability.

Persistent state should be stored under `data/`.

Current local files:

- `data/meetings/*.json`: generated meeting results.
- `data/bad_cases.jsonl`: bad-case review records.

The app can run without API credentials by using the deterministic fallback extractor. That fallback should be treated as a demo path, not as production extraction quality.
