import re


def sanitize_html(text: str) -> str:

    cleaned = re.sub(r"(?is)<script[^>]*>.*?</script>", "", text)

    cleaned = re.sub(r"(?is)<iframe[^>]*>.*?</iframe>", "", cleaned)

    cleaned = re.sub(r"(?is)<object[^>]*>.*?</object>", "", cleaned)

    cleaned = re.sub(r"(?is)<embed[^>]*>.*?</embed>", "", cleaned)

    cleaned = re.sub(r"(?i)\bon\w+\s*=", "data-blocked=", cleaned)

    cleaned = re.sub(r"(?i)javascript:", "blocked:", cleaned)

    return cleaned
