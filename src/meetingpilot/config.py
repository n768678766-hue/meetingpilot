"""Configuration helpers for MeetingPilot."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AppConfig:
    api_key: str | None
    base_url: str
    model: str


def load_config() -> AppConfig:
    return AppConfig(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
    )

