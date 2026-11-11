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


def test_use_mocks_defaults_to_true(monkeypatch):
    monkeypatch.delenv("USE_MOCKS", raising=False)
    assert config.load_settings().use_mocks is True


@pytest.mark.parametrize("value,expected", [("true", True), ("1", True), ("False", False), ("no", False)])
def test_use_mocks_parsing(monkeypatch, value, expected):
    monkeypatch.setenv("USE_MOCKS", value)
    assert config.load_settings().use_mocks is expected


def test_use_mocks_rejects_unknown_value(monkeypatch):
    monkeypatch.setenv("USE_MOCKS", "maybe")
    with pytest.raises(ValueError, match="USE_MOCKS"):
        config.load_settings()


def test_vision_timeout_default_and_validation(monkeypatch):
    monkeypatch.delenv("VISION_TIMEOUT_S", raising=False)
    assert config.load_settings().vision_timeout_s == 120.0
    monkeypatch.setenv("VISION_TIMEOUT_S", "30")
    assert config.load_settings().vision_timeout_s == 30.0
    for bad in ("abc", "0", "-5"):
        monkeypatch.setenv("VISION_TIMEOUT_S", bad)
        with pytest.raises(ValueError, match="VISION_TIMEOUT_S"):
            config.load_settings()
