# Cooked Crouton

Local Streamlit app (Ollama-powered). 100% local.

## Run

```
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt   # add requirements-dev.txt for tests (then: pytest)
copy .env.example .env
streamlit run app.py
```

## Mock mode

`USE_MOCKS=true` (default in `.env.example`) runs the app with fake vision, recipe and
chat services, so Ollama and the other modules are not needed. See `docs/integration.md`.

## Photo upload

JPG, PNG or WebP up to 10 MB. The image is validated by content, resized (max 1024 px),
re-encoded as JPEG without metadata, and kept in memory only (nothing is written to disk).

## Layout

- `app.py` entry point; `config.py` settings from `.env`
- `ui/` sidebar + the 3 areas (Upload & Analysis, Recipe & Dashboard, Chat)
- `contracts/` shared schemas; `services/` service interfaces, mocks and factory
- `components/` reusable widgets (image upload); `utils/` helpers (image processing, streaming)
- `assets/` static files
