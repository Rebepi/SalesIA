import re

from salesia.modules.auditoria.application.contracts.seguridad_sanitize_input import SanitizeInputRequest


def sanitize_input_text(payload: SanitizeInputRequest):
    clean = re.sub(r"(?i)<script[^>]*>.*?</script>", "", payload.raw_text, flags=re.DOTALL)
    clean = re.sub(r"(?i)on\w+\s*=\s*['\"][^'\"]*['\"]", "", clean)
    clean = re.sub(r"(?i)javascript:", "", clean)
    return {"original_length": len(payload.raw_text), "sanitized_text": clean, "is_modified": clean != payload.raw_text}
