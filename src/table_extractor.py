import pdfplumber


def extract_tables_from_pdf(pdf_path):
    """
    Scans every page of the PDF and extracts any tables found.
    Returns a list of dictionaries, one per table, containing:
    - page_number: which page the table was found on
    - markdown: the table converted into markdown format
    """
    tables_data = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()

            for table in tables:
                if table and len(table) > 1:  # skip empty or single-row tables
                    markdown = convert_table_to_markdown(table)
                    tables_data.append({
                        "page_number": page_number,
                        "markdown": markdown
                    })

    return tables_data


def convert_table_to_markdown(table):
    """
    Converts a raw table (list of rows, each row a list of cell values)
    into a markdown-formatted table string.
    """
    # Replace None values with empty strings
    cleaned_rows = []
    for row in table:
        cleaned_row = [cell if cell is not None else "" for cell in row]
        cleaned_rows.append(cleaned_row)

    header = cleaned_rows[0]
    body_rows = cleaned_rows[1:]

    # Build the markdown table
    markdown_lines = []
    markdown_lines.append("| " + " | ".join(header) + " |")
    markdown_lines.append("| " + " | ".join(["---"] * len(header)) + " |")

    for row in body_rows:
        markdown_lines.append("| " + " | ".join(row) + " |")

    return "\n".join(markdown_lines)


# The section below only runs when this file is executed directly.
# It is used for quick testing.
if __name__ == "__main__":
    test_pdf = "data/sample_filings/apple_10k.pdf"  # change this if your filename is different
    result = extract_tables_from_pdf(test_pdf)

    print(f"Total tables found: {len(result)}")
    print("--- Sample: first table found ---")
    if result:
        print(f"Found on page {result[0]['page_number']}")
        print(result[0]["markdown"])