"""Central configuration, loaded from environment variables / a local `.env` file."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _resolve_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else BASE_DIR / path


@dataclass(frozen=True)
class Settings:
    """Application settings. Defaults keep everything on localhost."""

    ollama_host: str
    ollama_port: int
    vision_model: str
    chat_model: str
    recipe_api_url: str
    upload_dir: Path
    data_dir: Path
    assets_dir: Path

    @property
    def ollama_url(self) -> str:
        return f"http://{self.ollama_host}:{self.ollama_port}"


def load_settings() -> Settings:
    """Build `Settings` from the current environment."""
    return Settings(
        ollama_host=os.getenv("OLLAMA_HOST", "127.0.0.1"),
        ollama_port=int(os.getenv("OLLAMA_PORT", "11434")),
        vision_model=os.getenv("OLLAMA_VISION_MODEL", "llava"),
        chat_model=os.getenv("OLLAMA_CHAT_MODEL", "llama3.1"),
        recipe_api_url=os.getenv("RECIPE_API_URL", ""),
        upload_dir=_resolve_path(os.getenv("UPLOAD_DIR", "uploads")),
        data_dir=_resolve_path(os.getenv("DATA_DIR", "data")),
        assets_dir=BASE_DIR / "assets",
    )


settings = load_settings()
