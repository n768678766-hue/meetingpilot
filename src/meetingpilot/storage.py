"""Local storage helpers for outputs and bad-case logs."""

import json
from datetime import datetime
from pathlib import Path

from meetingpilot.models import BadCase, MeetingResult


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_meeting_result(result: MeetingResult, data_dir: Path) -> Path:
    """Persist a meeting result as JSON. Returns the file path."""
    out_dir = data_dir / "meetings"
    _ensure_dir(out_dir)

    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    slug = result.title.lower().replace(" ", "-")[:40]
    filename = f"{timestamp}_{slug}.json"
    filepath = out_dir / filename

    filepath.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    return filepath


def load_meeting_history(data_dir: Path) -> list[MeetingResult]:
    """Load all saved meeting results, newest first."""
    out_dir = data_dir / "meetings"
    if not out_dir.exists():
        return []

    results: list[MeetingResult] = []
    for path in sorted(out_dir.glob("*.json"), reverse=True):
        try:
            results.append(MeetingResult.model_validate_json(path.read_text(encoding="utf-8")))
        except Exception:
            continue
    return results


def save_bad_case(bad_case: BadCase, data_dir: Path) -> Path:
    """Append a bad case record to a JSONL file. Returns the file path."""
    _ensure_dir(data_dir)
    filepath = data_dir / "bad_cases.jsonl"
    with filepath.open("a", encoding="utf-8") as handle:
        handle.write(bad_case.model_dump_json() + "\n")
    return filepath


def load_bad_cases(data_dir: Path) -> list[BadCase]:
    """Load all bad case records, newest first."""
    cases: list[BadCase] = []
    jsonl_path = data_dir / "bad_cases.jsonl"
    if jsonl_path.exists():
        for line in jsonl_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                cases.append(BadCase.model_validate_json(line))
            except Exception:
                continue

    legacy_dir = data_dir / "bad_cases"
    if legacy_dir.exists():
        for path in sorted(legacy_dir.glob("*.json"), reverse=True):
            try:
                cases.append(BadCase.model_validate_json(path.read_text(encoding="utf-8")))
            except Exception:
                continue

    return sorted(cases, key=lambda item: item.created_at, reverse=True)
