import re


def calculate_name_similarity(name1: str, name2: str) -> float:
    def tokenize(s: str) -> set[str]:
        words = re.sub(r"[^\w\s]", "", s.lower()).split()
        ignored = {"sac", "sa", "srl", "eirl", "corp", "de", "la", "el", "los", "las", "y", "llc", "inc"}
        return {w for w in words if w not in ignored and len(w) > 1}

    t1 = tokenize(name1)
    t2 = tokenize(name2)
    if not t1 or not t2:
        return 0.0
    inter = len(t1 & t2)
    union = len(t1 | t2)
    return float(inter / union) if union > 0 else 0.0
