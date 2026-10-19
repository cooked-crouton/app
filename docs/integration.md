# Integration contracts (PROPOSAL, to be agreed with the other deliverables)

Schemas live in [`contracts/`](../contracts) as Pydantic v2 models, the single source of
truth. Export JSON Schema with `Model.model_json_schema()`.

Deliverables: **D2** = vision engine + nutrition calculator (`vision_engine` repo),
**D3** = recipe generation + RAG Q&A (`rag_llm` repo), **D4** = this Streamlit app.

## Decision: how the app calls the other modules

**Mixed: D2 is imported as a Python module, D3 is called over local HTTP.**

- D3 already ships as a FastAPI service (ChromaDB + Ollama, docker-compose, `/api/v1/...`).
  Importing it would pull chromadb/langchain into the Streamlit environment, and its
  top-level `app` package clashes with our `app.py`. So: HTTP.
- The D2 deliverable is "un module Python documenté avec tests unitaires". It uses a local
  VLM through Ollama, so its own dependencies stay light. So: import, behind the
  `VisionEngine` protocol (`contracts/vision.py`).
  - Caveat: `vision_engine` currently requires Python >= 3.14 and prototypes with
    torch/timm. If D2 keeps those, or the Python versions cannot be aligned, fall back to a
    local HTTP wrapper around D2 with the same schemas. The contract does not change.
- Everything stays 100% local: only `localhost` URLs, set via `.env`. Follow-up: add
  `RECIPE_SERVICE_URL` (and `VISION_SERVICE_URL` if the fallback is used) to `config.py`,
  defaulting to localhost.
- D2 inference is slow: the app runs it outside the UI thread/with a spinner. HTTP calls use
  timeouts and show `ErrorResponse.detail` on failure.

## D2 interface (Python)

| Call | Input | Output |
|---|---|---|
| `analyze_image(image: bytes, portions=1)` | JPEG/PNG bytes | `NutritionAnalysis` |
| `analyze_ingredients(request)` | `AnalyzeIngredientsRequest` (names, optional grams) | `NutritionAnalysis` |

The text-only path exists because the assignment says D2 takes "une image ou une liste
d'ingrédients". Missing grams are estimated; given grams are kept as is.

## D3 endpoints (HTTP)

| Method + path | Request | Response |
|---|---|---|
| `POST /api/v1/recipes/generate` | `RecipeRequest` | `RecipeResponse` |
| `POST /api/v1/chat` | `ChatRequest` | `ChatResponse` |

Errors: non-2xx with `ErrorResponse` (`{"detail": "..."}`, the FastAPI default).

## Conventions

- Units: energy in kcal (optional, since the assignment only requires carbs, fats,
  proteins), everything else in grams. Field names are English snake_case.
- `macros_per_portion = total_macros / portions`; `total_macros` is the sum of ingredient
  macros. Not enforced by the schema.
- Cooking state: `raw`, `cooked` (type unknown), a cooking type, or `unknown`.
- Recipe generation ("frigo vide"): the recipe may only use the ingredients of `analysis`
  (plus basics the D3 owner defines, e.g. salt, water, oil). Stated here, enforced in D3's
  prompt.
- Conversation history: **stateless server**. The app keeps the chat persistent and sends
  the full prior turns (oldest first, excluding the new `question`) on every `/chat` call.
- Sources: **every chat answer must be sourced** (`ChatResponse.sources` has at least one
  entry). `title` required; `url`, `snippet`, `score` optional. `title` and `url` match
  the metadata the RAG store already keeps per recipe. Generation may return no sources.
- Free-text inputs are length-capped (question 2000 chars, 50 history turns, 20 constraints).
- Image upload safety (D2/app): accept only JPEG/PNG, cap the size, never trust client
  filenames.
- Privacy/local: nutrition reference data (e.g. Ciqual) is a local file. No call to
  OpenFoodFacts or any other online API at runtime. Model weights are pre-downloaded
  (document in the README).
- Environmental impact: the project requires a CodeCarbon analysis. Each module logs
  its emissions (D3 already lists `codecarbon`); the app only reads/reports them.
- D4 dashboard: pie charts of macros come from `Macros` (`protein_g`, `carbs_g`, `fat_g`).

## Open questions for the other owners

D2 (vision):
1. Final list of cooking states, and how the cooking type is detected.
2. Which nutrition database (Ciqual file?) and how it is bundled locally.
3. Can it run on the same Python version as the app, or do we need the HTTP fallback?
4. Which Ollama VLM and model name.

D3 (RAG):
5. Language of generated text (the RAG store is French; the app is currently English).
6. Shared Ollama instance and model names (`rag_llm` defaults to `http://ollama:11434`),
   ports (API uses 8080), and whether it runs in the same docker-compose.
7. Pantry basics allowed in "frigo vide" mode.
