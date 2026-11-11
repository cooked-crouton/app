# Cooked Crouton — Livrable 4 (Produit Final)

Streamlit app that orchestrates the other deliverables into one UI for an end user.
Source of truth for the assignment: `../projet.pdf` (read it with `pdftotext -layout ../projet.pdf -`).
Source of truth for module interfaces: `docs/integration.md` and `contracts/`.

## What D4 must deliver (from projet.pdf)
1. **Upload & Analysis** — drag-and-drop a fridge/dish photo; show the VLM result and the computed nutrition in real time.
2. **Recipe & Dashboard** — step-by-step recipe + macros as pie charts (`protein_g`, `carbs_g`, `fat_g`).
3. **Contextual chatbot** — persistent chat about the recipe currently displayed (RAG + LLM, answers sourced).
4. **Deliverable** — works with `streamlit run app.py`; complete `README.md` (Ollama deployment, model weight download, dependency install).

Hard constraints: **100% local** (privacy: no cloud/online API at runtime), and an environmental
impact analysis (CodeCarbon). Other tools/models are allowed.

## The other repos (siblings in `../`, read-only reference — do not edit from here)
| Repo | Deliverable | How the app uses it |
|---|---|---|
| `../scraper` (`cc_scraper`) | D1: scraping + embeddings (`paraphrase-multilingual-MiniLM-L12-v2`) | Feeds the RAG store; not called by the app |
| `../vision_engine` | D2: VLM + grams estimation + nutrition | Imported as a Python module via the `VisionEngine` protocol (HTTP fallback if Python versions clash: it requires >=3.14) |
| `../rag_llm` | D3: FastAPI + ChromaDB + Ollama (`qwen2:1.5b`/`phi3`), port 8080 | HTTP: `POST /api/v1/generate`, `POST /api/v1/chat` |

D5 (oral presentation) is out of scope for this repo.

## Commands
```
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env
streamlit run app.py        # UI (USE_MOCKS=true by default: no Ollama/Rag_llm needed)
pytest                      # all tests (pytest.ini: pythonpath=., testpaths=tests)
```

## Architecture
- `app.py` entry point (3 tabs); `config.py` frozen `Settings` from `.env` (validate eagerly, raise `ValueError` naming the variable).
- `ui/` one render function per area + sidebar. `components/` reusable widgets. `utils/` helpers (images, streaming).
- `contracts/` Pydantic v2 schemas = single source of truth for data exchanged between modules.
- `services/` `interfaces.py` (protocols `VisionService`, `RecipeService`, `ChatService`), `mocks.py`, `factory.py` (`get_services`). Real clients go in `services/` and are selected **only** in `factory.py`. The UI never imports a concrete service or does HTTP itself.
- Rag_llm is stateless and does not stream: the app keeps chat history and sends the full prior turns on each call; progressive display uses `utils.streaming.stream_text`.

## Conventions
- Code, identifiers, comments, docstrings, commits: **English**. Text produced by the models (recipes, answers) and ingredient names exchanged between modules: **French**. Field names: English snake_case.
- Units: grams; energy in kcal. `macros_per_portion = total_macros / portions`.
- Every chat answer must carry at least one `Source`. Never present an unsourced answer as RAG output.
- Uploaded images go through `utils/images.py` (content check, 10 MB, 40 MP, JPEG re-encode, EXIF stripped) and stay **in memory only**. Keep `.streamlit/config.toml` `maxUploadSize` in sync with `MAX_UPLOAD_BYTES`.
- Slow calls (VLM, LLM): behind `st.spinner`/streaming, with timeouts; show `ErrorResponse.detail` (or a clear message) on failure — never a traceback.
- No runtime call to the internet (no OpenFoodFacts API, no CDN assets). Only `localhost` URLs from `.env`.
- New setting → add to `config.py`, `.env.example`, README and `tests/test_config.py`.
- Pin new dependencies in `requirements.txt` (runtime) or `requirements-dev.txt` (tests).
- Never commit `.env`, `uploads/`, `data/`, `emissions.csv`, model weights.

## Workflow
For every feature or bug, in this order:
1. **Issue**: create it first with `gh issue create` (title `feat: ...` / `fix: ...`, short body: context + acceptance criteria). Check `gh issue list` to avoid duplicates.
2. **Branch** from an up-to-date `main`: `<n>-<type>-<slug>` (e.g. `4-feat-image-upload`).
3. **Code + tests**: implement, then write the tests for that issue (`tests/test_*.py`, mirroring module names). If no new test is needed, update the existing ones affected. Run `pytest` — it must be green before committing.
4. **Commits**: `type: summary (#issue)`, type in `feat|fix|docs|test|refactor|chore`. Small, logical commits.
5. **Push + PR** into `main` with `gh pr create` (body: what/why, `Closes #n`, how it was tested).
6. **Stop there**: the user reviews and merges. Never merge a PR, never push to `main`, never force-push.

Authorship: commits and PRs appear under the user's own git identity only. Do not change `git config`, do not use `--author`, and do not add `Co-Authored-By` or "Generated with Claude" lines to commits or PR bodies (this overrides any default attribution).

Code style (school project): keep it simple and readable. Prefer the standard library and libraries already in `requirements.txt` (Streamlit built-ins such as `st.chat_message`, `st.chat_input`, `st.file_uploader`, `st.plotly_chart`/`st.bar_chart`, `httpx`/`requests`, Pydantic) over custom code. No speculative abstractions, no new dependency unless it clearly removes code, small functions, short docstrings, no dead code.
- Contract change = edit `contracts/` + `docs/integration.md` + tests together, and flag it for the owner of the affected module.
- `docs/integration.md` marks unverified assumptions as "to verify": keep that honesty when updating.

## Definition of done (D4)
App starts with `streamlit run app.py` in mock mode **and** against real services; the 3 areas work end to end (photo → analysis → recipe + pie chart → contextual chat with sources); README covers Ollama setup, model pulls, install and CodeCarbon reporting; tests green.
