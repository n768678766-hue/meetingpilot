# Bad Case Log Design

Bad cases should capture examples where the AI output was not usable enough.

Suggested fields:

- `created_at`
- `transcript_excerpt`
- `expected_output`
- `actual_output`
- `issue_type`
- `severity`
- `prompt_version`
- `notes`

Common issue types:

- Owner missing.
- Due date missing.
- Task split too broad.
- Decision confused with action item.
- Risk point omitted.
- Hallucinated person or date.

## Storage

Bad cases are appended to:

```text
data/bad_cases.jsonl
```

Each line is one JSON object matching the `BadCase` Pydantic model. This makes the log easy to inspect, filter, and later convert into prompt regression examples.

## Review Loop

1. Run extraction on a real or sample transcript.
2. Compare the result against what a human would use after the meeting.
3. Record the smallest useful transcript excerpt, the actual output, and the expected fix.
4. Group recurring errors by issue type.
5. Update prompts or schemas only when multiple bad cases show the same failure pattern.
