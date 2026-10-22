"""Central configuration, loaded from environment variables / a local `.env` file."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _env(name: str, default: str) -> str:
    """Read an env var, treating unset or blank values as `default`."""
    return os.getenv(name, "").strip() or default


def _env_port(name: str, default: int) -> int:
    value = _env(name, str(default))
    try:
        port = int(value)
    except ValueError:
        raise ValueError(f"{name} must be an integer, got {value!r}") from None
    if not 1 <= port <= 65535:
        raise ValueError(f"{name} must be between 1 and 65535, got {port}")
    return port


def _env_bool(name: str, default: bool) -> bool:
    value = _env(name, str(default)).lower()
    if value in ("1", "true", "yes", "on"):
        return True
    if value in ("0", "false", "no", "off"):
        return False
    raise ValueError(f"{name} must be true or false, got {value!r}")


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
    use_mocks: bool
    upload_dir: Path
    data_dir: Path
    assets_dir: Path

    @property
    def ollama_url(self) -> str:
        return f"http://{self.ollama_host}:{self.ollama_port}"


def load_settings() -> Settings:
    """Build `Settings` from the current environment."""
    return Settings(
        ollama_host=_env("OLLAMA_HOST", "127.0.0.1"),
        ollama_port=_env_port("OLLAMA_PORT", 11434),
        vision_model=_env("OLLAMA_VISION_MODEL", "llava"),
        chat_model=_env("OLLAMA_CHAT_MODEL", "llama3.1"),
        recipe_api_url=_env("RECIPE_API_URL", ""),
        use_mocks=_env_bool("USE_MOCKS", True),
        upload_dir=_resolve_path(_env("UPLOAD_DIR", "uploads")),
        data_dir=_resolve_path(_env("DATA_DIR", "data")),
        assets_dir=BASE_DIR / "assets",
    )


settings = load_settings()
