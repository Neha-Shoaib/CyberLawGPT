import os
import re
import streamlit as st
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from groq import Groq

st.set_page_config(
    page_title="CyberLawGPT",
    page_icon="⚖️",
    layout="wide",
)

# -------------------------------------------------------------------
# CyberLawGPT
# Knowledge base manually structured from the supplied:
# Prevention of Electronic Crimes Act, 2016 (PECA 2016)
#
# The PDF is NOT required at runtime and is NOT uploaded by the user.
# The legal knowledge below is the application's built-in source.
# -------------------------------------------------------------------

LAW_DOCUMENT = [
    {
        "section": "Section 1 — Short title, extent and commencement",
        "topic": "Scope of the Act",
        "text": (
            "This law is the Prevention of Electronic Crimes Act, 2016. "
            "It is a law concerning prevention of electronic crimes and related "
            "matters in Pakistan."
        ),
    },
    {
        "section": "Section 2 — Definitions",
        "topic": "Unauthorized access",
        "text": (
            "Unauthorized access means access to an information system or data "
            "without authorization or beyond the authorization given to the person."
        ),
    },
    {
        "section": "Section 2 — Definitions",
        "topic": "Unauthorized interception",
        "text": (
            "Unauthorized interception concerns interception of information "
            "transmitted through an information system without lawful authorization."
        ),
    },
    {
        "section": "Section 2 — Definitions",
        "topic": "Information system",
        "text": (
            "The Act defines an information system in the context of systems "
            "used for generating, sending, receiving, storing or processing information."
        ),
    },
    {
        "section": "Section 2 — Definitions",
        "topic": "Critical infrastructure",
        "text": (
            "The Act defines critical infrastructure in relation to an information "
            "system or infrastructure whose disruption, destruction or compromise "
            "can affect important public or other critical functions."
        ),
    },
    {
        "section": "Section 2 — Definitions",
        "topic": "Service provider",
        "text": (
            "The Act includes a definition of service provider covering persons or "
            "entities that provide services relating to information systems or "
            "communication systems."
        ),
    },
    {
        "section": "Section 2 — Definitions",
        "topic": "Traffic data",
        "text": (
            "Traffic data concerns data relating to a communication, including "
            "information about the origin, destination, route, time, date, size, "
            "duration or type of underlying service or communication, as covered "
            "by the Act."
        ),
    },
    {
        "section": "Section 3 — Unauthorized access to information system or data",
        "topic": "Unauthorized access",
        "text": (
            "A person who intentionally gains unauthorized access to an information "
            "system or data is dealt with as an offence under the Act. The Act "
            "provides a punishment for unauthorized access."
        ),
    },
    {
        "section": "Section 4 — Unauthorized copying or transmission of data",
        "topic": "Copying or transmitting data",
        "text": (
            "Unauthorized copying or transmission of data is an offence under the "
            "Act where the conduct falls within the conditions prescribed by the section."
        ),
    },
    {
        "section": "Section 5 — Interference with or damage to information system or data",
        "topic": "Interference or damage",
        "text": (
            "Interference with or damage to an information system or data is "
            "criminalized by the Act where the statutory requirements of the section "
            "are satisfied."
        ),
    },
    {
        "section": "Section 6 — Unauthorized access to critical infrastructure information system or data",
        "topic": "Critical infrastructure access",
        "text": (
            "Unauthorized access to a critical infrastructure information system "
            "or data is treated as a specific offence under the Act and is subject "
            "to the punishment provided by the section."
        ),
    },
    {
        "section": "Chapter II — Offences and Punishments",
        "topic": "Electronic offences",
        "text": (
            "Chapter II establishes electronic offences and corresponding "
            "punishments. The Act addresses conduct including illegal access, "
            "unauthorized copying or transmission, interference or damage, and "
            "unauthorized access involving critical infrastructure."
        ),
    },
    {
        "section": "Statement of Objects and Reasons",
        "topic": "Purpose and covered cybercrime",
        "text": (
            "The Act addresses cybercrime-related conduct including illegal access "
            "or hacking, interference such as denial-of-service or distributed "
            "denial-of-service activity, electronic forgery and fraud, cyber terrorism, "
            "unauthorized interception, malicious code and identity-related offences."
        ),
    },
    {
        "section": "Chapter — Prosecution and Trial",
        "topic": "Prosecution and trial",
        "text": (
            "The Act contains provisions dealing with prosecution and trial of "
            "offences under the Act, including provisions concerning cognizance, "
            "bailability and compoundability as provided by the Act."
        ),
    },
    {
        "section": "Chapter — Compensation",
        "topic": "Compensation",
        "text": (
            "The Act contains provisions concerning compensation in connection "
            "with matters covered by the Act, subject to the statutory requirements."
        ),
    },
    {
        "section": "Chapter — Investigation and Forensic Procedures",
        "topic": "Investigation",
        "text": (
            "The Act provides a legal framework concerning investigation of "
            "electronic crimes and forensic procedures, including provisions "
            "relating to the investigation agency and forensic processes."
        ),
    },
    {
        "section": "Chapter — Relation with Other Laws",
        "topic": "Other laws",
        "text": (
            "The Act contains provisions concerning its relationship with other "
            "laws. Questions about another Pakistani statute should not be answered "
            "as though that statute were contained in this Act."
        ),
    },
    {
        "section": "Chapter — Rule Making",
        "topic": "Rules",
        "text": (
            "The Act provides for rule-making concerning matters covered by the Act."
        ),
    },
]

# Add a compact legal index with the high-level concepts explicitly identified
# in the supplied document's objects/reasons section.
LAW_DOCUMENT.extend([
    {
        "section": "PECA 2016 — Core legal concepts",
        "topic": "Hacking / illegal access",
        "text": (
            "Illegal access or hacking is identified among the forms of electronic "
            "crime addressed by the Act. The relevant statutory provisions should "
            "be applied according to their specific elements and section wording."
        ),
    },
    {
        "section": "PECA 2016 — Core legal concepts",
        "topic": "Denial of service",
        "text": (
            "Interference including denial-of-service and distributed denial-of-service "
            "activity is identified in the Act's statement of objects as cybercrime "
            "conduct addressed by the legislation."
        ),
    },
    {
        "section": "PECA 2016 — Core legal concepts",
        "topic": "Electronic forgery and fraud",
        "text": (
            "Electronic forgery and electronic fraud are identified in the Act's "
            "statement of objects as forms of electronic crime addressed by the law."
        ),
    },
    {
        "section": "PECA 2016 — Core legal concepts",
        "topic": "Cyber terrorism",
        "text": (
            "Cyber terrorism is identified in the Act's statement of objects as "
            "conduct addressed by the electronic-crimes legislation."
        ),
    },
    {
        "section": "PECA 2016 — Core legal concepts",
        "topic": "Malicious code",
        "text": (
            "Malicious code is identified in the Act's statement of objects as "
            "a category of cybercrime-related conduct addressed by the legislation."
        ),
    },
    {
        "section": "PECA 2016 — Core legal concepts",
        "topic": "Identity theft",
        "text": (
            "Identity theft is identified in the Act's statement of objects as "
            "electronic-crime conduct addressed by the legislation."
        ),
    },
])

def chunk_text(text, max_chars=850, overlap=120):
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start, end)
            if boundary > start + 300:
                end = boundary
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return chunks

@st.cache_resource(show_spinner="Loading legal knowledge base...")
def build_index():
    records = []
    for item in LAW_DOCUMENT:
        for i, chunk in enumerate(chunk_text(item["text"])):
            records.append({
                "section": item["section"],
                "topic": item["topic"],
                "text": chunk,
                "chunk": i + 1,
            })

    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    embeddings = model.encode(
        [r["text"] for r in records],
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    embeddings = np.asarray(embeddings, dtype="float32")

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    return model, index, records

def retrieve(question, model, index, records, top_k):
    q = model.encode([question], normalize_embeddings=True)
    q = np.asarray(q, dtype="float32")
    scores, ids = index.search(q, min(top_k, len(records)))

    results = []
    for score, idx in zip(scores[0], ids[0]):
        if idx < 0:
            continue
        item = dict(records[idx])
        item["score"] = float(score)
        results.append(item)
    return results

def answer_with_groq(question, context, technicality, response_size,
                     language, practical_example, caution):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("GROQ_API_KEY is not configured.")
        st.info("For Streamlit Cloud, add GROQ_API_KEY under Settings → Secrets.")
        st.stop()

    model_name = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    client = Groq(api_key=api_key)

    language_instruction = {
        "English": "Answer in English.",
        "Urdu": "Answer in Urdu script.",
        "Roman Urdu": "Answer in Roman Urdu.",
    }[language]

    size_instruction = {
        "Short": "Give a concise answer with only the necessary legal points.",
        "Medium": "Give a clear answer with the relevant law and a brief explanation.",
        "Detailed": "Give a detailed answer with the relevant legal provisions, explanation, and implications.",
        "Very detailed": "Give a comprehensive but focused answer, explaining the relevant provisions and how they relate to the question.",
    }[response_size]

    example_instruction = (
        "Include one clearly labeled practical example if it helps explain the law."
        if practical_example else
        "Do not include a practical example unless essential."
    )

    caution_instruction = (
        "End with a brief legal-information caution that this is not a substitute "
        "for advice from a qualified Pakistani legal professional."
        if caution else
        "Do not add a separate disclaimer paragraph."
    )

    prompt = f"""
You are CyberLawGPT, a legal-information assistant grounded ONLY in the
built-in knowledge extracted and structured from the supplied Prevention of
Electronic Crimes Act, 2016 (PECA 2016).

USER QUESTION:
{question}

RELEVANT BUILT-IN LEGAL MATERIAL:
{context}

STRICT RULES:
1. Base the answer only on the supplied legal material.
2. Do not invent a section number, punishment, fine, imprisonment period,
   procedure, exception, authority, definition, or legal test.
3. If the supplied material is insufficient, explicitly say:
   "The available PECA 2016 material in CyberLawGPT does not provide enough
   information to answer that reliably."
4. Do not treat a general mention in the Statement of Objects and Reasons as
   proof of every element or punishment of a specific offence.
5. When a precise punishment or statutory requirement is not present in the
   built-in material, say that it is not available rather than guessing.
6. Distinguish definitions, offences, purposes, and procedural provisions.
7. Do not claim that PECA covers a matter merely because it sounds like a
   cybercrime; connect the answer to the retrieved material.
8. Do not present this as a lawyer-client relationship or case-specific legal
   advice.
9. Preserve statutory wording such as "may extend to" when that wording is
   actually present in the supplied material.
10. If the question asks about a different Pakistani law that is not represented
    in the built-in PECA material, clearly state that limitation.

TECHNICALITY:
{technicality}

RESPONSE SIZE:
{size_instruction}

LANGUAGE:
{language_instruction}

EXAMPLE:
{example_instruction}

CAUTION:
{caution_instruction}

Answer now.
"""

    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a careful legal-information assistant. "
                    "Never fabricate legal facts."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=1800 if response_size in ["Detailed", "Very detailed"] else 1000,
    )
    return completion.choices[0].message.content

# ------------------------- UI ---------------------------------------

st.title("⚖️ CyberLawGPT")
st.caption(
    "RAG-based Pakistani cyber-law assistant grounded in the "
    "Prevention of Electronic Crimes Act, 2016 (PECA)."
)

with st.sidebar:
    st.header("⚙️ Answer Settings")

    technicality = st.selectbox(
        "Technicality",
        ["Simple", "Balanced", "Technical", "Legal / Technical"],
        index=1,
    )

    response_size = st.selectbox(
        "Response size",
        ["Short", "Medium", "Detailed", "Very detailed"],
        index=1,
    )

    language = st.selectbox(
        "Language",
        ["English", "Urdu", "Roman Urdu"],
        index=0,
    )

    top_k = st.slider(
        "Retrieved legal passages",
        min_value=2,
        max_value=10,
        value=5,
    )

    practical_example = st.checkbox(
        "Include a practical example",
        value=True,
    )

    caution = st.checkbox(
        "Show legal-information caution",
        value=True,
    )

    st.divider()

    st.subheader("Knowledge Source")
    st.success("PECA 2016 knowledge is built into the application.")
    st.caption(
        "No PDF upload is required at runtime. The application uses a "
        "FAISS vector index generated from the structured legal knowledge."
    )

    st.divider()
    st.caption("Model: openai/gpt-oss-120b via Groq")
    st.caption("Embeddings: all-MiniLM-L6-v2")

model, index, records = build_index()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input(
    "Ask a question about an electronic crime under PECA 2016..."
)

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Finding the relevant PECA provisions..."):
            results = retrieve(question, model, index, records, top_k)

            context_parts = []
            for i, r in enumerate(results, 1):
                context_parts.append(
                    f"[Source {i}]\n"
                    f"Section/Part: {r['section']}\n"
                    f"Topic: {r['topic']}\n"
                    f"Material: {r['text']}"
                )

            context = "\n\n".join(context_parts)
            response = answer_with_groq(
                question,
                context,
                technicality,
                response_size,
                language,
                practical_example,
                caution,
            )

        st.markdown(response)

        with st.expander("🔎 Retrieved legal material used"):
            for i, r in enumerate(results, 1):
                st.markdown(
                    f"**{i}. {r['section']}** — {r['topic']}  \n"
                    f"Similarity: `{r['score']:.3f}`"
                )
                st.write(r["text"])
                st.divider()

        st.session_state.messages.append(
            {"role": "assistant", "content": response}
        )

st.divider()
st.caption(
    "CyberLawGPT provides informational answers based on its built-in "
    "PECA 2016 knowledge. It is not a law firm and does not create an "
    "advocate-client relationship. For a real case, consult a qualified "
    "legal professional in Pakistan."
)
