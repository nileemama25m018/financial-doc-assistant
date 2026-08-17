import re


def normalize_comparison_question(question, document_labels=None):
    """
    Converts company-specific comparison questions into a generic metric question.

    Comparison mode queries each document independently, so company names in the
    question can cause refusals or wrong labels. This keeps the metric intent
    while removing entity names that belong in the document label, not the query.
    """
    normalized = question.strip()

    labels = list(document_labels or [])
    labels.extend([
        "Apple", "Microsoft", "Alphabet", "Google", "Amazon", "Meta",
        "Tesla", "NVIDIA", "Netflix", "IBM", "Oracle"
    ])

    for label in labels:
        if not label:
            continue
        escaped = re.escape(label)
        normalized = re.sub(rf"\b{escaped}\'s\b", "", normalized, flags=re.IGNORECASE)
        normalized = re.sub(rf"\b{escaped}\b", "", normalized, flags=re.IGNORECASE)

    normalized = re.sub(r"\b(compare|comparison of|between|across|versus|vs\.?)\b", "", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\s+", " ", normalized).strip(" ,.-")
    normalized = re.sub(r"^(and\s+)|(\s+and)$", "", normalized, flags=re.IGNORECASE).strip(" ,.-")

    if normalized and not re.match(r"^(what|how|which|where|when|why|is|are|was|were|did|does|do)\b", normalized, flags=re.IGNORECASE):
        normalized = "What was " + normalized

    if not normalized.endswith("?"):
        normalized = normalized.rstrip(".") + "?"

    return normalized or question.strip()
