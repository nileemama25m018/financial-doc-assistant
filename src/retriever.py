from sentence_transformers import CrossEncoder

# Loading the cross-encoder model once when this module is imported.
_reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def retrieve_and_rerank(vector_store, query_text, initial_top_k=10, final_top_k=5):
    """
    Two-stage retrieval:
    1. FAISS quickly finds 'initial_top_k' roughly-relevant chunks.
    2. The cross-encoder carefully re-scores those chunks against the query,
       and we keep only the best 'final_top_k' of them.
    """
    # Stage 1: fast, rough retrieval from FAISS
    candidates = vector_store.search(query_text, top_k=initial_top_k)

    # Stage 2: cross-encoder scores each (query, chunk_text) pair
    pairs = [(query_text, chunk["text"]) for chunk in candidates]
    scores = _reranker.predict(pairs)

    # Attach scores to their chunks, then sort by score (highest first)
    scored_chunks = list(zip(candidates, scores))
    scored_chunks.sort(key=lambda x: x[1], reverse=True)

    # Keep only the top final_top_k after re-ranking
    top_chunks = [chunk for chunk, score in scored_chunks[:final_top_k]]

    return top_chunks


# The section below only runs when this file is executed directly.
# It is used for quick testing.
if __name__ == "__main__":
    from src.chunker import build_all_chunks
    from src.vector_store import VectorStore

    test_pdf = "data/sample_filings/apple_10k.pdf"
    chunks = build_all_chunks(test_pdf)

    store = VectorStore()
    store.build(chunks)

    query = "What was Apple's total revenue?"
    results = retrieve_and_rerank(store, query)

    print(f"--- Top {len(results)} re-ranked results for query: '{query}' ---")
    for i, result in enumerate(results, start=1):
        print(f"\nResult {i} (page {result['page_number']}, type: {result['chunk_type']}):")
        print(result["text"][:300])