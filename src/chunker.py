from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.pdf_processor import extract_text_from_pdf
from src.table_extractor import extract_tables_from_pdf


def chunk_prose(pages_data, chunk_size=800, chunk_overlap=100):
    """
    Splits page-level prose text into smaller overlapping chunks.
    chunk_size: roughly how many characters per chunk
    chunk_overlap: how many characters repeat between chunks,
                   so context isn't lost at the boundary
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    prose_chunks = []
    for page in pages_data:
        pieces = splitter.split_text(page["text"])
        for piece in pieces:
            prose_chunks.append({
                "chunk_type": "prose",
                "page_number": page["page_number"],
                "text": piece
            })

    return prose_chunks


def chunk_tables(tables_data):
    """
    Turns each extracted table into its own chunk.
    Tables are NOT split further, to keep rows and columns intact.
    """
    table_chunks = []
    for table in tables_data:
        table_chunks.append({
            "chunk_type": "table",
            "page_number": table["page_number"],
            "text": table["markdown"]
        })

    return table_chunks


def build_all_chunks(pdf_path):
    """
    Runs both prose and table extraction + chunking for one PDF,
    and returns a single combined list of chunks.
    """
    pages_data = extract_text_from_pdf(pdf_path)
    tables_data = extract_tables_from_pdf(pdf_path)

    prose_chunks = chunk_prose(pages_data)
    table_chunks = chunk_tables(tables_data)

    all_chunks = prose_chunks + table_chunks
    return all_chunks


# The section below only runs when this file is executed directly.
# It is used for quick testing.
if __name__ == "__main__":
    test_pdf = "data/sample_filings/apple_10k.pdf"  # change this if your filename is different
    chunks = build_all_chunks(test_pdf)

    prose_count = len([c for c in chunks if c["chunk_type"] == "prose"])
    table_count = len([c for c in chunks if c["chunk_type"] == "table"])

    print(f"Total chunks: {len(chunks)}")
    print(f"Prose chunks: {prose_count}")
    print(f"Table chunks: {table_count}")
    print("--- Sample prose chunk ---")
    print(chunks[0]["text"][:300])