# Integration contracts (PROPOSAL, to be agreed with the other deliverables)

Schemas live in [`contracts/`](../contracts) as Pydantic v2 models, the single source of
truth. Export JSON Schema with `Model.model_json_schema()`.

Modules: **vision_engine** = vision engine + nutrition calculator, **Rag_llm** = recipe
generation + RAG Q&A (repo `rag_llm`), **D4** = this Streamlit app.

## Decision: how the app calls the other modules

**Mixed: vision_engine is imported as a Python module, Rag_llm is called over local HTTP.**

- Rag_llm already ships as a FastAPI service (ChromaDB + Ollama, docker-compose, `/api/v1/...`).
  Importing it would pull chromadb/langchain into the Streamlit environment, and its
  top-level `app` package clashes with our `app.py`. So: HTTP.
- The vision_engine deliverable is "un module Python documenté avec tests unitaires". It uses a local
  VLM through Ollama, so its own dependencies stay light. So: import, behind the
  `VisionEngine` protocol (`contracts/vision.py`).
  - Caveat: `vision_engine` currently requires Python >= 3.14 and prototypes with
    torch/timm. If vision_engine keeps those, or the Python versions cannot be aligned, fall back to a
    local HTTP wrapper around vision_engine with the same schemas. The contract does not change.
- Everything stays 100% local: only `localhost` URLs, set via `.env`. Follow-up: add
  `RECIPE_SERVICE_URL` (and `VISION_SERVICE_URL` if the fallback is used) to `config.py`,
  defaulting to localhost.
- vision_engine inference is slow: the app runs it outside the UI thread/with a spinner. HTTP calls use
  timeouts and show `ErrorResponse.detail` on failure.

## vision_engine interface (Python)

| Call | Input | Output |
|---|---|---|
| `analyze_image(image: bytes, portions=1)` | JPEG/PNG bytes | `NutritionAnalysis` |
| `analyze_ingredients(request)` | `AnalyzeIngredientsRequest` (names, optional grams) | `NutritionAnalysis` |

### Errors vision_engine must raise (`contracts/vision.py`)

| Exception | Meaning | Message shown by the app |
|---|---|---|
| `VisionUnavailableError` | Ollama cannot be reached | start it with `ollama serve` |
| `VisionModelNotFoundError` | VLM not installed | `ollama pull <model>` |
| `VisionTimeoutError` | analysis too slow | try a smaller photo / retry |
| `ValueError` | invalid input (e.g. empty image) | the message itself |

Any other exception gives a generic "failed unexpectedly" message (details only in logs).
The app also gives up after `VISION_TIMEOUT_S` (default 120 s) and lets the user cancel.
Python cannot kill a running call, so cancel/timeout only make the app ignore the late
result. `analyze_image` returns the whole result at once: the app reveals ingredients
progressively on its own. Real partial results would need a streaming call from
vision_engine (optional request, not needed for now).

The text-only path exists because the assignment says vision_engine takes "une image ou une liste
d'ingrédients". Missing grams are estimated; given grams are kept as is.

## Rag_llm endpoints (HTTP)

| Method + path | Request | Response |
|---|---|---|
| `POST /api/v1/generate` | `RecipeRequest` (`ingredients`, `dietary_constraints`) | `RecipeResponse` (`status`, `recipe`) |
| `POST /api/v1/chat` | `ChatRequest` (`message`, `history`) | `ChatResponse` (`status`, `data`) |

The schemas mirror the Rag_llm README (API at `http://localhost:8080`, Swagger on `/docs`).
Both responses carry `emissions_kgco2eq` (CodeCarbon) that the app can display and sum.
Errors: assumed non-2xx with `ErrorResponse` (`{"detail": "..."}`, the FastAPI default);
**to verify** against the running API.

### Consequences of the Rag_llm API (workarounds, no change requested yet)

- `/generate` takes ingredient **names** only and returns `used_ingredients` without
  quantities. Macros shown with a recipe come from the vision_engine analysis, filtered on
  `used_ingredients`. Servings and max cook time are not supported.
- `/chat` has no recipe context field. The app puts the displayed recipe in `history` as a
  first message. If the small LLM copes badly with it, ask Rag_llm for a dedicated field.
- `/chat` returns free text. "Adapt the recipe" (issue #13) is done by calling `/generate`
  again with an extra dietary constraint.
- Rag_llm does not stream. The app streams client-side with `utils.streaming.stream_text`.

## Conventions

- Units: energy in kcal (optional, since the assignment only requires carbs, fats,
  proteins), everything else in grams. Field names are English snake_case.
- `macros_per_portion = total_macros / portions`; `total_macros` is the sum of ingredient
  macros. Not enforced by the schema.
- Cooking state: `raw`, `cooked` (type unknown), a cooking type, or `unknown`.
- Recipe generation ("frigo vide"): the recipe may only use the given ingredients, plus a
  fixed list of pantry basics (salt, pepper, water, oil). Enforced in Rag_llm's prompt.
  Build the request from an analysis with `RecipeRequest.from_analysis`.
- Language (agreed with Rag_llm): all generated text (recipe, answers) is **French**.
  Ingredient names exchanged between modules are therefore **French** too (this also
  matches Ciqual). Field names stay English snake_case.
- Conversation history: **stateless server**. The app keeps the chat persistent and sends
  the full prior turns (oldest first, excluding the new `message`) on every `/chat` call.
- Sources: **every chat answer must be sourced** (`ChatData.sources` has at least one
  entry). `title` required, `url` optional, matching the metadata the RAG store keeps per
  recipe. Generation returns no sources.
- Free-text inputs are length-capped (message 2000 chars, 50 history turns, 20 dietary constraints).
- Image upload safety: the app (`utils/images.py`) checks the file content (JPG/PNG/WebP,
  10 MB, 40 MP), re-encodes it as JPEG (max side 1024 px, EXIF/GPS dropped) and keeps it in
  memory only. vision_engine therefore always receives clean JPEG bytes.
- Privacy/local: nutrition reference data (e.g. Ciqual) is a local file. No call to
  OpenFoodFacts or any other online API at runtime. Model weights are pre-downloaded
  (document in the README).
- Environmental impact: the project requires a CodeCarbon analysis. Each module logs
  its emissions (Rag_llm already lists `codecarbon`); the app only reads/reports them.
- D4 dashboard: pie charts of macros come from `Macros` (`protein_g`, `carbs_g`, `fat_g`).

## Open questions for the other owners

vision_engine (vision):
1. Final list of cooking states, and how the cooking type is detected.
2. Which nutrition database (Ciqual file?) and how it is bundled locally.
3. Can it run on the same Python version as the app, or do we need the HTTP fallback?
4. Which Ollama VLM and model name.

Rag_llm (RAG):
5. Docker: should the app share Rag_llm's docker-compose (and its Ollama on port 11434)?
   Known from its README: LLM `qwen2:1.5b` or `phi3`, API on port 8080. The embedding model
   is `paraphrase-multilingual-MiniLM-L12-v2`, but `rag_llm/app/config.py` still says
   `all-minilm`; scraped vectors and query vectors must use the same model.
6. Error format of `/generate` and `/chat` (verify on the running API).
7. Later, only if the workarounds above prove insufficient: recipe context field in
   `/chat`, structured recipe in chat answers, quantities in `/generate`.

## Mock services (`USE_MOCKS=true`, default)

`services/` holds the interfaces the UI uses (`VisionService`, `RecipeService`,
`ChatService`), the mocks (`mocks.py`) and `get_services(settings)` (`factory.py`), which
returns the mocks when `USE_MOCKS=true`. The real clients will implement the same
interfaces, so swapping needs no UI change.
