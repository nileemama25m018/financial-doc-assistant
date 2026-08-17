import faiss
import numpy as np
import pickle

from src.embeddings import generate_embeddings


class VectorStore:
    """
    Wraps a FAISS index along with the original chunk data (text + metadata),
    so we can go from "closest matching numbers" back to "actual readable text".
    """

    def __init__(self):
        self.index = None
        self.chunks = []  # stores the original chunk dictionaries, in the same order as the embeddings

    def build(self, chunks):
        """
        Takes a list of chunk dictionaries (each with a "text" key),
        generates embeddings for all of them, and builds a FAISS index.
        """
        self.chunks = chunks
        texts = [chunk["text"] for chunk in chunks]

        embeddings = generate_embeddings(texts)
        embeddings = np.array(embeddings).astype("float32")

        dimension = embeddings.shape[1]  # length of each embedding vector (384 for our model)
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)

    def search(self, query_text, top_k=5):
        """
        Takes a question (query_text), converts it into an embedding,
        and returns the top_k most similar chunks from the store.
        """
        query_embedding = generate_embeddings([query_text])
        query_embedding = np.array(query_embedding).astype("float32")

        distances, indices = self.index.search(query_embedding, top_k)

        results = []
        for idx in indices[0]:
            results.append(self.chunks[idx])

        return results

    def save(self, folder_path):
        """Saves the FAISS index and chunk data to disk, so we don't have to rebuild every time."""
        faiss.write_index(self.index, f"{folder_path}/index.faiss")
        with open(f"{folder_path}/chunks.pkl", "wb") as f:
            pickle.dump(self.chunks, f)

    def load(self, folder_path):
        """Loads a previously saved FAISS index and chunk data from disk."""
        self.index = faiss.read_index(f"{folder_path}/index.faiss")
        with open(f"{folder_path}/chunks.pkl", "rb") as f:
            self.chunks = pickle.load(f)


# The section below only runs when this file is executed directly.
# It is used for quick testing.
if __name__ == "__main__":
    from src.chunker import build_all_chunks

    test_pdf = "data/sample_filings/apple_10k.pdf"
    chunks = build_all_chunks(test_pdf)

    store = VectorStore()
    store.build(chunks)

    print(f"Total chunks indexed: {len(store.chunks)}")

    query = "What was Apple's total revenue?"
    results = store.search(query, top_k=3)

    print(f"\n--- Top 3 results for query: '{query}' ---")
    for i, result in enumerate(results, start=1):
        print(f"\nResult {i} (page {result['page_number']}, type: {result['chunk_type']}):")
        print(result["text"][:300])