---
paths:
  - "ui/**/*.py"
  - "components/**/*.py"
  - "app.py"
---

# Streamlit UI rules

- One `render_*()` function per area, no business logic inside: call services from `get_services(settings)`.
- Persist state in `st.session_state` with namespaced keys (`analysis`, `recipe`, `chat_history`); initialise with `setdefault`.
  Chat history and the current recipe must survive reruns and tab switches.
- Long operations: `st.spinner` or `st.write_stream`; never block without feedback.
- Macros charts: pie (`protein_g`, `carbs_g`, `fat_g`), per portion and total; handle all-zero macros without crashing.
- Show the sources of every chat answer under the message.
- User-visible errors: `st.error` with a short message; no raw exceptions.
- UI labels are English (current code); model-generated content stays French.
- Keep logic in pure helpers testable without Streamlit; optionally smoke-test with `streamlit.testing.v1.AppTest`.
