from sentence_transformers import SentenceTransformer

# Loading the embedding model. This happens once when the module is imported.
# The model file will be downloaded automatically the first time this runs.
_model = SentenceTransformer("BAAI/bge-small-en-v1.5")


def generate_embeddings(text_list):
    """
    Takes a list of text strings and returns a list of embeddings
    (each embedding is a list of numbers representing the meaning of the text).
    """
    embeddings = _model.encode(text_list, show_progress_bar=True)
    return embeddings


# The section below only runs when this file is executed directly.
# It is used for quick testing.
if __name__ == "__main__":
    sample_texts = [
        "Apple's revenue grew 8% year over year.",
        "The company reported total assets of $350 billion."
    ]
    result = generate_embeddings(sample_texts)

    print(f"Number of embeddings generated: {len(result)}")
    print(f"Length of each embedding vector: {len(result[0])}")
    print("--- First few numbers of embedding 1 ---")
    print(result[0][:5])