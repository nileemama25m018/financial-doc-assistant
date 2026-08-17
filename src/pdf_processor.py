from pypdf import PdfReader

def extract_text_from_pdf(pdf_path):
    """
    Takes a PDF file path and returns a list of dictionaries,
    one per page, containing the page number and its extracted text.
    """
    reader = PdfReader(pdf_path)
    pages_data = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if text and text.strip():  # skip empty pages
            pages_data.append({
                "page_number": page_number,
                "text": text
            })

    return pages_data


# The section below only runs when this file is executed directly.
# It is used for quick testing.
if __name__ == "__main__":
    test_pdf = "data/sample_filings/apple_10k.pdf"  # change this if your filename is different
    result = extract_text_from_pdf(test_pdf)

    print(f"Total pages with text: {len(result)}")
    print("--- Sample from Page 1 ---")
    print(result[0]["text"][:500])  # show first 500 characters