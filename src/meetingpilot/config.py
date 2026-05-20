"""Configuration helpers for MeetingPilot."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AppConfig:
    api_key: str | None
    base_url: str
    model: str


def _clean_api_key(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None

    value = raw_value.strip().strip('"').strip("'")
    if not value:
        return None

    lowered = value.lower()
    placeholder_markers = ["your", "<", ">", "你的", "key"]
    if any(marker in lowered for marker in placeholder_markers):
        return None

    try:
        value.encode("ascii")
    except UnicodeEncodeError:
        return None

    return value


def load_config() -> AppConfig:
    return AppConfig(
        api_key=_clean_api_key(os.getenv("OPENAI_API_KEY")),
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
    )
