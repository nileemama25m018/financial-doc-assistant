from src.chunker import build_all_chunks
from src.vector_store import VectorStore
from src.retriever import retrieve_and_rerank
from src.llm import generate_answer
from src.verifier import verify_answer
from src.query_normalizer import normalize_comparison_question


def build_store_for_document(pdf_path):
    """
    Runs the full pipeline (extraction + chunking + embedding)
    for a single PDF, and returns a ready-to-query VectorStore.
    """
    chunks = build_all_chunks(pdf_path)
    store = VectorStore()
    store.build(chunks)
    return store


def compare_metric_across_documents(document_paths, metric_question):
    """
    Runs retrieval + answer generation + verification separately per document.
    Company/entity names are removed from the comparison query to avoid
    cross-document refusals and wrong labels.
    """
    comparison_results = []
    normalized_question = normalize_comparison_question(metric_question, document_paths.keys())

    for doc_label, pdf_path in document_paths.items():
        store = build_store_for_document(pdf_path)

        top_chunks = retrieve_and_rerank(store, normalized_question)
        answer = generate_answer(top_chunks, normalized_question)
        verification = verify_answer(answer, top_chunks)

        top_source_page = top_chunks[0]["page_number"] if top_chunks else None

        comparison_results.append({
            "document": doc_label,
            "question_used": normalized_question,
            "answer": answer,
            "source_page": top_source_page,
            "fully_verified": verification["is_fully_verified"]
        })

    return comparison_results


if __name__ == "__main__":
    document_paths = {
        "Apple 10-K": "data/sample_filings/apple_10k.pdf",
        "Microsoft 10-K": "data/sample_filings/microsoft_10k.pdf"
    }

    question = "Compare total revenue between Apple and Microsoft."
    results = compare_metric_across_documents(document_paths, question)

    print(f"--- Comparison for: '{question}' ---\n")
    for result in results:
        print(f"Document: {result['document']}")
        print(f"Question used: {result['question_used']}")
        print(f"Answer: {result['answer']}")
        print(f"Source page: {result['source_page']}")
        print(f"Fully verified: {result['fully_verified']}")
        print("-" * 50)
