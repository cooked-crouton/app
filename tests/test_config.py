from pathlib import Path

import config


def test_defaults_are_local(monkeypatch):
    for key in ("OLLAMA_HOST", "OLLAMA_PORT", "UPLOAD_DIR"):
        monkeypatch.delenv(key, raising=False)
    s = config.load_settings()
    assert s.ollama_url == "http://127.0.0.1:11434"
    assert s.upload_dir == config.BASE_DIR / "uploads"


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("OLLAMA_HOST", "localhost")
    monkeypatch.setenv("OLLAMA_PORT", "9999")
    monkeypatch.setenv("UPLOAD_DIR", str(Path.cwd()))
    s = config.load_settings()
    assert s.ollama_url == "http://localhost:9999"
    assert s.upload_dir == Path.cwd()
