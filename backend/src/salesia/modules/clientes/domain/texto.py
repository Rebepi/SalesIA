import html
import re
from typing import Optional


def sanitize_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = re.sub(r"<[^>]+>", "", value)
    return html.escape(cleaned).strip()
