from pathlib import Path

import pytest

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


def test_blank_values_fall_back_to_defaults(monkeypatch):
    monkeypatch.setenv("OLLAMA_HOST", "  ")
    monkeypatch.setenv("OLLAMA_PORT", "")
    s = config.load_settings()
    assert s.ollama_url == "http://127.0.0.1:11434"


@pytest.mark.parametrize("port", ["abc", "0", "70000"])
def test_invalid_port_raises(monkeypatch, port):
    monkeypatch.setenv("OLLAMA_PORT", port)
    with pytest.raises(ValueError, match="OLLAMA_PORT"):
        config.load_settings()
