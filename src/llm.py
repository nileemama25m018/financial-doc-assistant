import os
from dotenv import load_dotenv
from groq import Groq

from src.prompts import build_prompt

# Load the GROQ_API_KEY and optional GROQ_MODEL from the .env file
load_dotenv()

_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

DEFAULT_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")
FALLBACK_MODELS = [
    DEFAULT_MODEL,
    "openai/gpt-oss-120b",
    "qwen/qwen3.6-27b",
]


def generate_answer(retrieved_chunks, user_question, model=None):
    """
    Sends the retrieved context + question to Groq and returns the answer.
    Tries fallback models because Groq model availability can change over time.
    """
    prompt = build_prompt(retrieved_chunks, user_question)
    models_to_try = [model] if model else FALLBACK_MODELS
    last_error = None

    for model_name in dict.fromkeys(models_to_try):
        try:
            response = _client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as exc:
            last_error = exc
            error_code = getattr(exc, "status_code", None)
            if error_code not in (400, 404):
                raise

    raise RuntimeError(
        "No configured Groq model is available. Set GROQ_MODEL in .env to a model enabled for your account."
    ) from last_error


if __name__ == "__main__":
    from src.chunker import build_all_chunks
    from src.vector_store import VectorStore
    from src.retriever import retrieve_and_rerank

    test_pdf = "data/sample_filings/apple_10k.pdf"
    chunks = build_all_chunks(test_pdf)

    store = VectorStore()
    store.build(chunks)

    query = "What was Apple's total revenue?"
    top_chunks = retrieve_and_rerank(store, query)

    answer = generate_answer(top_chunks, query)

    print(f"--- Question: {query} ---")
    print(f"\n--- Answer ---\n{answer}")
