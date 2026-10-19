# Integration contracts (PROPOSAL, to be agreed with the other deliverables)

Schemas live in [`contracts/`](../contracts) as Pydantic v2 models, the single source of
truth. Export JSON Schema with `Model.model_json_schema()`.

## Decision: how the app calls the other modules

**Local HTTP (FastAPI), not Python imports.**

- The recipe/RAG module already ships as a FastAPI service (ChromaDB + Ollama, docker-compose,
  `/api/v1/...`). Importing it would pull chromadb/langchain into the Streamlit environment,
  and its top-level `app` package clashes with our `app.py`.
- Modules stay independently runnable and testable, so teams can work in parallel.
- Stays 100% local: only `localhost` URLs, set via `.env`. Follow-up: add
  `VISION_SERVICE_URL` / `RECIPE_SERVICE_URL` to `config.py`, defaulting to localhost.
- Streamlit calls them synchronously with timeouts and shows `ErrorResponse.detail` on failure.

## Endpoints

| Module | Method + path | Request | Response |
|---|---|---|---|
| Vision/nutrition | `POST /api/v1/analyze` | multipart: `image` file + `AnalyzeImageRequest` fields | `NutritionAnalysis` |
| Recipe | `POST /api/v1/recipes/generate` | `RecipeRequest` | `RecipeResponse` |
| Q&A | `POST /api/v1/chat` | `ChatRequest` | `ChatResponse` |

Errors: non-2xx with `ErrorResponse` (`{"detail": "..."}`, the FastAPI default).

## Conventions

- Units: energy in kcal, everything else in grams. Field names are English snake_case.
- `macros_per_portion = total_macros / portions`; `total_macros` is the sum of ingredient macros.
- Conversation history: **stateless server**. The app sends the full prior turns (oldest
  first, excluding the new `question`) on every `/chat` call.
- Sources: `title` required; `url`, `snippet`, `score` optional. `title` and `url` match the
  metadata the RAG store already keeps per recipe.
- Free-text inputs are length-capped (question 2000 chars, 50 history turns, 20 constraints).
- Image upload safety (vision side): accept only JPEG/PNG, cap the size, never trust filenames.

## Open questions

1. The cloned `rag_llm` repo is called D2 but contains the recipe RAG (ingestion only so far),
   not vision/nutrition. Who owns which endpoint? The issue lists vision/nutrition as D2 and
   recipe/Q&A as D3.
2. Language of generated text (the RAG store is French; the app is currently English).
3. Shared Ollama instance and model names (`rag_llm` defaults to `http://ollama:11434`).
4. Ports (`rag_llm` API uses 8080) and whether both modules run in one docker-compose.
