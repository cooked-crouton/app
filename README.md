# Cooked Crouton

Local Streamlit app (Ollama-powered). 100% local.

## Run

```
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
streamlit run app.py
```

## Layout

- `app.py` entry point; `config.py` settings from `.env`
- `ui/` sidebar + the 3 areas (Upload & Analysis, Recipe & Dashboard, Chat)
- `services/`, `components/`, `utils/`, `assets/` reserved for upcoming issues
