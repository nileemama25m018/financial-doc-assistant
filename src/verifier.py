import re


def extract_numbers(text):
    """
    Extracts numeric tokens from a piece of text using regex.
    Catches formats like: 416,161  $416,161  8.2%  391,035.5

    Page references like "Page 33" are removed first, so page numbers
    don't get mistaken for financial figures.
    """
    # Remove "Page <number>" mentions before extracting numbers,
    # since these are source citations, not financial data.
    text_without_page_refs = re.sub(r"[Pp]age\s+\d+", "", text)

    # This pattern catches numbers with optional $ sign, commas, decimals, and % sign
    pattern = r"\$?\d[\d,]*\.?\d*%?"
    raw_matches = re.findall(pattern, text_without_page_refs)

    cleaned_numbers = set()
    for match in raw_matches:
        cleaned = match.replace("$", "").replace(",", "").replace("%", "")
        # Ignore tiny numbers like single digits (e.g. "1", "2025" as a year is fine to keep)
        if cleaned and len(cleaned.replace(".", "")) >= 2:
            cleaned_numbers.add(cleaned)

    return cleaned_numbers


def verify_answer(answer_text, retrieved_chunks):
    """
    Checks whether the numbers mentioned in the answer actually appear
    in the retrieved context chunks.
    Returns a dictionary with verification results.
    """
    answer_numbers = extract_numbers(answer_text)

    # Combine all retrieved context into one big text blob to search against
    combined_context = " ".join(chunk["text"] for chunk in retrieved_chunks)
    context_numbers = extract_numbers(combined_context)

    verified = []
    unverified = []

    for number in answer_numbers:
        if number in context_numbers:
            verified.append(number)
        else:
            unverified.append(number)

    is_fully_verified = len(unverified) == 0

    return {
        "is_fully_verified": is_fully_verified,
        "verified_numbers": verified,
        "unverified_numbers": unverified
    }


# The section below only runs when this file is executed directly.
# It is used for quick testing.
if __name__ == "__main__":
    from src.chunker import build_all_chunks
    from src.vector_store import VectorStore
    from src.retriever import retrieve_and_rerank
    from src.llm import generate_answer

    test_pdf = "data/sample_filings/apple_10k.pdf"
    chunks = build_all_chunks(test_pdf)

    store = VectorStore()
    store.build(chunks)

    query = "What was Apple's total revenue?"
    top_chunks = retrieve_and_rerank(store, query)
    answer = generate_answer(top_chunks, query)

    verification = verify_answer(answer, top_chunks)

    print(f"--- Answer ---\n{answer}")
    print(f"\n--- Verification ---")
    print(f"Fully verified: {verification['is_fully_verified']}")
    print(f"Verified numbers: {verification['verified_numbers']}")
    print(f"Unverified numbers: {verification['unverified_numbers']}")