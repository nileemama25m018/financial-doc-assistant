import streamlit as st
import tempfile
import os

from src.chunker import build_all_chunks
from src.vector_store import VectorStore
from src.retriever import retrieve_and_rerank
from src.llm import generate_answer
from src.verifier import verify_answer
from src.query_normalizer import normalize_comparison_question


st.set_page_config(page_title="Financial Document Intelligence Assistant", layout="wide", page_icon="💠")

# ---------------- CUSTOM STYLING ----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: radial-gradient(circle at 20% 0%, #131a24 0%, #0d1117 45%, #0a0d12 100%);
    }

    /* Hide default Streamlit chrome for a cleaner look */
    #MainMenu, footer, header {visibility: hidden;}

    /* Custom header card */
    .app-header {
        background: linear-gradient(135deg, #161b22 0%, #1c2333 100%);
        border: 1px solid #2d3542;
        border-radius: 16px;
        padding: 2rem 2.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 24px rgba(0,0,0,0.35);
    }
    .app-header-title {
        font-size: 2.1rem;
        font-weight: 800;
        background: linear-gradient(90deg, #58a6ff, #79c0ff 60%, #a5d6ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .app-header-sub {
        color: #8b949e;
        font-size: 1rem;
        margin-top: 0.4rem;
    }
    .badge-row {
        margin-top: 1.1rem;
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
    }
    .badge {
        background: #1c2333;
        border: 1px solid #30363d;
        color: #79c0ff;
        font-size: 0.78rem;
        font-weight: 600;
        padding: 0.3rem 0.75rem;
        border-radius: 999px;
        letter-spacing: 0.3px;
    }

    /* Section cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #131a24;
        border: 1px solid #2d3542 !important;
        border-radius: 14px !important;
        padding: 0.5rem;
    }

    /* Radio buttons as segmented control */
    div[role="radiogroup"] {
        gap: 0.6rem;
    }
    div[role="radiogroup"] label {
        background-color: #161b22;
        border: 1px solid #2d3542;
        border-radius: 10px;
        padding: 10px 20px;
        transition: all 0.2s ease;
    }
    div[role="radiogroup"] label:hover {
        border-color: #58a6ff;
    }

    /* Buttons */
    .stButton button {
        background: linear-gradient(90deg, #238636, #2ea043);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.55rem 1.6rem;
        font-weight: 600;
        letter-spacing: 0.2px;
        transition: all 0.2s ease;
    }
    .stButton button:hover {
        background: linear-gradient(90deg, #2ea043, #3fb950);
        box-shadow: 0 4px 14px rgba(46, 160, 67, 0.45);
        transform: translateY(-1px);
    }

    /* Text inputs */
    .stTextInput input {
        background-color: #161b22;
        border: 1px solid #2d3542;
        border-radius: 10px;
        color: #e6edf3;
        padding: 0.6rem 0.9rem;
    }
    .stTextInput input:focus {
        border-color: #58a6ff;
        box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.15);
    }

    /* File uploader */
    section[data-testid="stFileUploaderDropzone"] {
        background-color: #161b22;
        border: 2px dashed #2d3542;
        border-radius: 12px;
    }

    /* Alerts (verification badges) */
    div[data-testid="stAlert"] {
        border-radius: 12px;
        padding: 1rem 1.2rem;
        font-weight: 500;
    }

    /* Headings */
    h2, h3 {
        color: #e6edf3 !important;
        font-weight: 700 !important;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: #161b22;
        border: 1px solid #2d3542;
        border-radius: 12px;
        padding: 1rem;
    }

    /* Table (comparison results) */
    table {
        border-radius: 10px;
        overflow: hidden;
    }

    /* Expander */
    details {
        background-color: #10151c;
        border: 1px solid #2d3542;
        border-radius: 10px;
        padding: 0.6rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown("""
<div class="app-header">
    <div class="app-header-title">Financial Document Intelligence Assistant</div>
    <div class="app-header-sub">Grounded Q&A over financial filings — every number traced back to its source, or flagged if it can't be.</div>
    <div class="badge-row">
        <span class="badge">FAISS Retrieval</span>
        <span class="badge">Cross-Encoder Re-ranking</span>
        <span class="badge">Table-Aware Extraction</span>
        <span class="badge">Numeric Verification</span>
    </div>
</div>
""", unsafe_allow_html=True)

mode = st.radio("Select mode:", ["Single Document", "Compare Across Documents"], label_visibility="collapsed")
st.write("")


def save_uploaded_file(uploaded_file):
    """Saves a Streamlit-uploaded file to a temporary path on disk, and returns that path."""
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, uploaded_file.name)
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return temp_path


def display_verification_badge(is_verified):
    """Shows a green or yellow badge depending on whether the answer's numbers were verified."""
    if is_verified:
        st.success("✅ All numbers in this answer were verified against the source document.")
    else:
        st.warning("⚠️ Some numbers in this answer could not be verified against the retrieved sources.")


# ---------------- SINGLE DOCUMENT MODE ----------------
if mode == "Single Document":
    with st.container(border=True):
        st.markdown("### 📄 Upload Document")
        uploaded_file = st.file_uploader("Upload a financial PDF", type=["pdf"], label_visibility="collapsed")

        if uploaded_file is not None:
            if st.button("Process Document", use_container_width=False):
                with st.spinner("Extracting text, tables, and building the search index... this may take a minute."):
                    pdf_path = save_uploaded_file(uploaded_file)
                    chunks = build_all_chunks(pdf_path)
                    store = VectorStore()
                    store.build(chunks)
                    st.session_state["store"] = store
                    st.session_state["chunk_count"] = len(chunks)
                    st.session_state["table_count"] = len([c for c in chunks if c["chunk_type"] == "table"])
                st.success(f"Document processed! {len(chunks)} chunks indexed.")

    if "store" in st.session_state:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Chunks Indexed", st.session_state["chunk_count"])
        col2.metric("Table Chunks", st.session_state["table_count"])
        col3.metric("Prose Chunks", st.session_state["chunk_count"] - st.session_state["table_count"])

        st.write("")
        with st.container(border=True):
            st.markdown("### 💬 Ask a Question")
            question = st.text_input("Ask a question about this document:", label_visibility="collapsed",
                                      placeholder="e.g. What was total revenue in 2025?")
            if question and st.button("Get Answer"):
                with st.spinner("Retrieving relevant sections and generating answer..."):
                    top_chunks = retrieve_and_rerank(st.session_state["store"], question)
                    answer = generate_answer(top_chunks, question)
                    verification = verify_answer(answer, top_chunks)

                st.markdown("#### Answer")
                st.write(answer)
                display_verification_badge(verification["is_fully_verified"])

                if verification["unverified_numbers"]:
                    st.write("Unverified numbers:", verification["unverified_numbers"])

                with st.expander("🔍 View retrieved sources"):
                    for i, chunk in enumerate(top_chunks, start=1):
                        st.markdown(f"**Source {i} — Page {chunk['page_number']} ({chunk['chunk_type']})**")
                        st.text(chunk["text"][:500])


# ---------------- COMPARISON MODE ----------------
else:
    with st.container(border=True):
        st.markdown("### 📄 Upload Documents")
        col1, col2 = st.columns(2)
        with col1:
            file_a = st.file_uploader("Upload Document A", type=["pdf"], key="doc_a")
            label_a = st.text_input("Label for Document A", value="Document A")
        with col2:
            file_b = st.file_uploader("Upload Document B", type=["pdf"], key="doc_b")
            label_b = st.text_input("Label for Document B", value="Document B")

        if file_a is not None and file_b is not None:
            if st.button("Process Both Documents"):
                with st.spinner("Processing both documents... this may take a couple of minutes."):
                    path_a = save_uploaded_file(file_a)
                    path_b = save_uploaded_file(file_b)

                    store_a = VectorStore()
                    store_a.build(build_all_chunks(path_a))

                    store_b = VectorStore()
                    store_b.build(build_all_chunks(path_b))

                    st.session_state["store_a"] = store_a
                    st.session_state["store_b"] = store_b
                st.success("Both documents processed!")

    if "store_a" in st.session_state and "store_b" in st.session_state:
        st.write("")
        with st.container(border=True):
            st.markdown("### 💬 Compare a Metric")
            question = st.text_input(
                "Enter the metric/question to compare:",
                label_visibility="collapsed",
                placeholder="e.g. What was total revenue?"
            )
            if question and st.button("Compare"):
                with st.spinner("Retrieving and generating answers for both documents..."):
                    normalized_question = normalize_comparison_question(question, [label_a, label_b])
                    results = []
                    for label, store in [(label_a, st.session_state["store_a"]), (label_b, st.session_state["store_b"])]:
                        top_chunks = retrieve_and_rerank(store, normalized_question)
                        answer = generate_answer(top_chunks, normalized_question)
                        verification = verify_answer(answer, top_chunks)
                        source_pages = sorted({chunk["page_number"] for chunk in top_chunks})
                        results.append({
                            "Document": label,
                            "Metric Query": normalized_question,
                            "Answer": answer,
                            "Source Pages": ", ".join(str(page) for page in source_pages[:3]),
                            "Verified": "✅" if verification["is_fully_verified"] else "⚠️"
                        })

                st.markdown("#### Comparison Results")
                st.table(results)
