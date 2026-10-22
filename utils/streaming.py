"""Client-side streaming for answers that arrive complete (use with `st.write_stream`)."""

import time
from collections.abc import Iterator


def stream_text(text: str, delay: float = 0.03) -> Iterator[str]:
    """Yield `text` word by word, keeping whitespace, pausing `delay` s between words."""
    words = text.split(" ")
    for i, word in enumerate(words):
        last = i == len(words) - 1
        yield word if last else word + " "
        if not last:
            time.sleep(delay)
