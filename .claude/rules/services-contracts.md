---
paths:
  - "services/**/*.py"
  - "contracts/**/*.py"
---

# Services & contracts rules

- Pydantic v2 only. Validate responses from other modules with the contract models; surface validation failures as clear errors.
- Real HTTP clients (Rag_llm): localhost URL from settings, explicit timeout, handle connection refused and non-2xx (`ErrorResponse`), no retry loops.
- Implement the protocols in `services/interfaces.py`; mocks and real clients must stay interchangeable.
- Mocks return deterministic, schema-valid data (including >=1 source for chat).
- Never call an online API; nutrition reference data is a local file.
- Any contract change updates `docs/integration.md` and `tests/test_contracts.py`.
