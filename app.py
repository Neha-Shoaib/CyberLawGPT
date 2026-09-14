import os
import re
import hashlib
import tempfile
from io import BytesIO

import faiss
import fitz  # PyMuPDF
import numpy as np
import requests
import streamlit as st
from groq import Groq
from sentence_transformers import SentenceTransformer


# ============================================================
# CyberLawGPT
# RAG chatbot for Pakistan's cyber-law PDF
# Stack: Streamlit + FAISS + Sentence Transformers + PyMuPDF + Groq
# ============================================================

APP_NAME = "CyberLawGPT"
DEFAULT_MODEL = "openai/gpt-oss-120b"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Put your public PDF URL in Streamlit Secrets:
# CYBER_LAW_PDF_URL = "https://....../cyber-law.pdf"
#
# The attached source used while developing this app is the
# Prevention of Electronic Crimes Act, 2016 (PECA 2016), as
# contained in the supplied PDF. The app intentionally uses the
# exact PDF supplied/configured by the user as its legal corpus.
PDF_URL = os.getenv("CYBER_LAW_PDF_URL", "").strip()


st.set_page_config(
    page_title=APP_NAME,
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -----------------------------
# Styling
# -----------------------------
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.7rem;
        font-weight: 800;
        margin-bottom: 0.1rem;
    }
    .subtitle {
        color: #6b7280;
        font-size: 1.05rem;
        margin-bottom: 1.2rem;
    }
    .source-box {
        border: 1px solid rgba(128,128,128,.25);
        border-radius: 12px;
        padding: 12px 16px;
        margin: 8px 0;
    }
    .disclaimer {
        font-size: .85rem;
        color: #6b7280;
        border-top: 1px solid rgba(128,128,128,.2);
        padding-top: 12px;
        margin-top: 25px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Secrets / API
# -----------------------------
def get_secret(name: str, default: str = "") -> str:
    """Read Streamlit secrets first, then environment variables."""
    try:
        value = st.secrets.get(name, "")
        if value:
            return str(value).strip()
    except Exception:
        pass
    return os.getenv(name, default).strip()


GROQ_API_KEY = get_secret("GROQ_API_KEY")
CONFIGURED_PDF_URL = get_secret("CYBER_LAW_PDF_URL", PDF_URL)
GROQ_MODEL = get_secret("GROQ_MODEL", DEFAULT_MODEL)


# -----------------------------
# PDF extraction + chunking
# -----------------------------
def download_pdf(url: str) -> bytes:
    """Download a PDF from a public URL."""
    headers = {"User-Agent": "CyberLawGPT/1.0"}
    response = requests.get(url, headers=headers, timeout=60)
    response.raise_for_status()

    content_type = response.headers.get("content-type", "").lower()
    if "pdf" not in content_type and not response.content.startswith(b"%PDF"):
        raise ValueError("The configured URL did not return a PDF file.")

    return response.content


def extract_pdf_pages(pdf_bytes: bytes):
    """Extract page-level text from the legal PDF."""
    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []

    for page_number, page in enumerate(document, start=1):
        text = page.get_text("text").strip()
        if text:
            pages.append(
                {
                    "page": page_number,
                    "text": text,
                }
            )

    document.close()

    if not pages:
        raise ValueError(
            "No selectable text was found in the PDF. "
            "This version expects a text-based PDF."
        )

    return pages


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def detect_section(text: str) -> str:
    """
    Detect common PECA-style section headings.
    This is metadata only; the model must rely on retrieved text.
    """
    patterns = [
        r"(?im)^\s*(\d+[A-Z]?)\.\s+([^\n]+)",
        r"(?im)^\s*section\s+(\d+[A-Z]?)\s*[:.-]?\s*([^\n]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return f"Section {match.group(1)} — {match.group(2).strip()[:140]}"

    return "Section not confidently detected"


def chunk_pages(pages, chunk_size=1100, overlap=180):
    """
    Character-based chunks preserve page/section metadata.
    Overlap helps avoid losing legal context at chunk boundaries.
    """
    chunks = []

    for page in pages:
        text = clean_text(page["text"])
        if not text:
            continue

        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    {
                        "text": chunk_text,
                        "page": page["page"],
                        "section": detect_section(chunk_text),
                    }
                )

            if end >= len(text):
                break

            start = max(end - overlap, start + 1)

    return chunks


# -----------------------------
# Embeddings + FAISS
# -----------------------------
@st.cache_resource(show_spinner="Loading embedding model...")
def load_embedding_model():
    return SentenceTransformer(DEFAULT_EMBEDDING_MODEL)


@st.cache_resource(show_spinner="Building legal-law vector index...")
def build_index(pdf_bytes: bytes, source_id: str):
    # source_id is intentionally part of the cache signature so that
    # a changed PDF creates a fresh FAISS index.
    del source_id

    pages = extract_pdf_pages(pdf_bytes)
    chunks = chunk_pages(pages)

    if not chunks:
        raise ValueError("No usable text chunks were created from the PDF.")

    model = load_embedding_model()
    texts = [item["text"] for item in chunks]

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    ).astype("float32")

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    return index, chunks


def retrieve(query: str, index, chunks, top_k: int = 5):
    model = load_embedding_model()

    query_embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    ).astype("float32")

    k = min(top_k, index.ntotal)
    scores, ids = index.search(query_embedding, k)

    results = []
    for score, idx in zip(scores[0], ids[0]):
        if idx < 0:
            continue

        item = chunks[int(idx)].copy()
        item["score"] = float(score)
        results.append(item)

    return results


# -----------------------------
# Groq answer generation
# -----------------------------
def build_prompt(
    question: str,
    contexts,
    technicality: str,
    response_size: str,
    language: str,
    include_practical: bool,
    include_caution: bool,
):
    context_text = "\n\n".join(
        [
            (
                f"[SOURCE {i} | PDF page {item['page']} | "
                f"{item['section']} | similarity={item['score']:.3f}]\n"
                f"{item['text']}"
            )
            for i, item in enumerate(contexts, start=1)
        ]
    )

    practical_instruction = (
        "If useful, give a short practical example clearly labeled as an example. "
        if include_practical
        else "Do not add a practical example unless necessary."
    )

    caution_instruction = (
        "End with a short note that this is informational and not a substitute for advice from a qualified Pakistani lawyer. "
        if include_caution
        else "Do not add a generic legal disclaimer."
    )

    return f"""
You are CyberLawGPT, a retrieval-augmented legal information assistant.

JURISDICTION:
Pakistan.

PRIMARY LEGAL SOURCE:
The user-provided cyber-law PDF. Treat the retrieved passages below as the authoritative
source for this answer. Do not silently replace them with another law or an internet source.

STRICT RAG RULES:
1. Answer ONLY from the supplied retrieved passages.
2. If the retrieved passages do not contain enough information, say:
   "The supplied PDF does not provide enough information to answer that reliably."
3. Never invent a section number, punishment, fine, procedure, authority, definition,
   exception, deadline, or legal conclusion.
4. Distinguish clearly between what the Act states and your plain-language explanation.
5. When possible, identify the relevant section number and PDF page.
6. Do not claim that an action is definitely legal/illegal based only on general knowledge.
7. If the question concerns a specific real-life dispute, explain the relevant provision
   but avoid pretending to provide a case-specific legal opinion.
8. For questions asking about penalties, preserve the wording "may extend to" when the
   source uses that wording.
9. Do not cite sources that are not present in the retrieved passages.

USER SETTINGS:
Technicality: {technicality}
Response size: {response_size}
Preferred language: {language}
{practical_instruction}
{caution_instruction}

RETRIEVED LEGAL PASSAGES:
{context_text}

QUESTION:
{question}

ANSWER FORMAT:
- Give the direct answer first.
- Then explain the relevant legal provision(s).
- Include section number(s) and PDF page number(s) when supported by the context.
- For penalties, use a compact bullet list.
""".strip()


def generate_answer(prompt: str) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add it to Streamlit Secrets or as an environment variable."
        )

    client = Groq(api_key=GROQ_API_KEY)

    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a careful Pakistan cyber-law information assistant. "
                    "You must follow the supplied RAG context and must not fabricate law."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=1800,
    )

    return completion.choices[0].message.content.strip()


# -----------------------------
# Source loading
# -----------------------------
@st.cache_data(show_spinner="Downloading cyber-law PDF...")
def get_remote_pdf(url: str):
    return download_pdf(url)


def load_source_pdf():
    """
    Priority:
    1. Uploaded PDF during the current session.
    2. Public PDF URL from CYBER_LAW_PDF_URL.
    """
    uploaded = st.session_state.get("uploaded_pdf_bytes")
    if uploaded:
        return uploaded, "uploaded-pdf"

    if CONFIGURED_PDF_URL:
        data = get_remote_pdf(CONFIGURED_PDF_URL)
        digest = hashlib.sha256(data).hexdigest()
        return data, digest

    return None, None


# -----------------------------
# UI
# -----------------------------
st.markdown('<div class="main-title">⚖️ CyberLawGPT</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">'
    "Ask questions about Pakistan's cyber law using a FAISS + semantic-search RAG pipeline."
    "</div>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("⚙️ Answer Controls")

    technicality = st.select_slider(
        "Technicality level",
        options=["Simple", "Balanced", "Technical", "Legal/Technical"],
        value="Balanced",
        help="Controls how technical and legally detailed the explanation should be.",
    )

    response_size = st.select_slider(
        "Response size",
        options=["Short", "Medium", "Detailed", "Very detailed"],
        value="Medium",
    )

    language = st.selectbox(
        "Answer language",
        ["English", "Urdu", "Roman Urdu"],
        index=0,
    )

    top_k = st.slider(
        "Retrieved legal passages",
        min_value=2,
        max_value=10,
        value=5,
        help="Higher values provide more source context but may be less focused.",
    )

    include_practical = st.checkbox(
        "Include practical example",
        value=True,
    )

    include_caution = st.checkbox(
        "Include legal-information caution",
        value=True,
    )

    st.divider()
    st.header("📄 Legal Source")

    uploaded_file = st.file_uploader(
        "Optional: upload a cyber-law PDF",
        type=["pdf"],
        help="If supplied, this PDF is used instead of the configured remote PDF.",
    )

    if uploaded_file is not None:
        st.session_state["uploaded_pdf_bytes"] = uploaded_file.getvalue()
        st.success("Uploaded PDF selected.")
    elif "uploaded_pdf_bytes" in st.session_state:
        if st.button("Clear uploaded PDF"):
            del st.session_state["uploaded_pdf_bytes"]
            st.rerun()

    if CONFIGURED_PDF_URL:
        st.caption("A default PDF URL is configured.")
    else:
        st.warning(
            "No CYBER_LAW_PDF_URL is configured. Upload a PDF above or add the URL "
            "to Streamlit Secrets."
        )

    st.divider()
    st.caption(
        "Model: " + GROQ_MODEL + "\n\n"
        "Embeddings: all-MiniLM-L6-v2\n\n"
        "Vector store: FAISS"
    )


# Load/build index
try:
    pdf_bytes, source_id = load_source_pdf()

    if pdf_bytes is None:
        st.info(
            "Upload the supplied cyber-law PDF from the sidebar, or configure "
            "`CYBER_LAW_PDF_URL` in Streamlit Secrets."
        )
        st.stop()

    index, chunks = build_index(pdf_bytes, source_id)

    st.success(
        f"Legal knowledge base ready — {len(chunks)} searchable passages indexed."
    )

except Exception as exc:
    st.error(f"Could not initialize the legal knowledge base: {exc}")
    st.stop()


# -----------------------------
# Chat state
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hello! I’m **CyberLawGPT**. Ask me about a cyber-law issue in Pakistan, "
                "and I’ll retrieve relevant provisions from the configured legal PDF."
            ),
        }
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


question = st.chat_input(
    "Example: What is the punishment for unauthorized access under the Act?"
)

if question:
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching the legal corpus and generating an answer..."):
            try:
                results = retrieve(question, index, chunks, top_k=top_k)

                if not results:
                    answer = (
                        "The supplied PDF does not provide enough information to answer "
                        "that reliably."
                    )
                    st.markdown(answer)
                else:
                    prompt = build_prompt(
                        question=question,
                        contexts=results,
                        technicality=technicality,
                        response_size=response_size,
                        language=language,
                        include_practical=include_practical,
                        include_caution=include_caution,
                    )

                    answer = generate_answer(prompt)
                    st.markdown(answer)

                    with st.expander("📚 Retrieved legal sources"):
                        for i, item in enumerate(results, start=1):
                            st.markdown(
                                f"**Source {i} — PDF page {item['page']} — "
                                f"{item['section']} — similarity {item['score']:.3f}**"
                            )
                            st.write(item["text"])

                st.session_state.messages.append(
                    {"role": "assistant", "content": answer}
                )

            except Exception as exc:
                error_message = f"Sorry, the answer could not be generated: {exc}"
                st.error(error_message)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_message}
                )


st.markdown(
    '<div class="disclaimer">'
    "CyberLawGPT is a document-grounded informational tool. It is not a law firm, "
    "does not create an advocate-client relationship, and should not replace advice "
    "from a qualified Pakistani legal professional. Answers are limited to the "
    "configured/uploaded PDF."
    "</div>",
    unsafe_allow_html=True,
)
