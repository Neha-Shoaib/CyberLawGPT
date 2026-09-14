⚖️ CyberLawGPT

CyberLawGPT is a Retrieval-Augmented Generation (RAG) application for asking questions about Pakistan's cyber law.

It uses:

Python

Streamlit — web UI

PyMuPDF — PDF text extraction

Sentence Transformers — semantic embeddings

FAISS — vector similarity search

Groq API — LLM answer generation

openai/gpt-oss-120b — default Groq model

The legal knowledge base is the cyber-law PDF supplied/configured by the user. The app is designed so that answers are grounded in retrieved passages rather than general model knowledge.

The supplied PDF used for this project is the Prevention of Electronic Crimes Act, 2016 (PECA 2016). The document states that the Act is called the Prevention of Electronic Crimes Act, 2016 and extends to the whole of Pakistan. It also describes its purpose as addressing unauthorized acts involving information systems and related offences, investigation, prosecution and trial.

1. How CyberLawGPT works

The app follows this pipeline:

Cyber-law PDF
     ↓
PyMuPDF text extraction
     ↓
Text cleaning + overlapping chunks
     ↓
Sentence Transformer embeddings
     ↓
FAISS vector index
     ↓
User question
     ↓
Question embedding
     ↓
Top-k relevant legal passages
     ↓
Groq / openai/gpt-oss-120b
     ↓
Grounded legal explanation

The app builds the FAISS index automatically when the source PDF is first loaded.

2. Important: only three project files

This project contains exactly these three code/document files:

CyberLawGPT/
├── app.py
├── requirements.txt
└── README.md

The PDF is not required to be committed as a fourth project file.

Instead, you can either:

Upload the PDF through the Streamlit sidebar, or

Configure a public PDF URL using CYBER_LAW_PDF_URL.

For Streamlit Cloud, option 2 is convenient if you have hosted the PDF at a stable public URL.

3. Groq API key

Create a Groq API key from your Groq account.

For local/Colab execution:

export GROQ_API_KEY="your_key_here"

On Windows PowerShell:

$env:GROQ_API_KEY="your_key_here"

For Streamlit Cloud:

Go to:

Your App → Settings → Secrets

Add:

GROQ_API_KEY = "your_groq_api_key"
CYBER_LAW_PDF_URL = "https://your-public-host/cyber-law.pdf"
GROQ_MODEL = "openai/gpt-oss-120b"

Do not commit your API key to GitHub.

4. Source PDF

The application is intentionally document-grounded.

For the supplied project PDF, use the Prevention of Electronic Crimes Act, 2016 document.

The PDF includes provisions covering subjects such as:

Unauthorized access

Unauthorized copying/transmission

Interference with information systems/data

Critical infrastructure offences

Cyber terrorism

Electronic forgery

Electronic fraud

Identity information

Unauthorized SIM issuance

Unauthorized interception

Offences against dignity

Offences involving modesty/minors

Malicious code

Cyber stalking

Spamming

Spoofing

Investigation powers

Preservation/acquisition of data

Traffic-data retention

Search and seizure

Disclosure of content data

Real-time collection

Forensic laboratory

Confidentiality

International cooperation

Prosecution and trial

The source document also contains definitions and procedural provisions. CyberLawGPT retrieves the relevant portions before asking the language model to formulate the response.

5. Run locally

Install dependencies:

pip install -r requirements.txt

Then:

streamlit run app.py

Open the local Streamlit URL shown in the terminal.

6. Run on Google Colab

In a Colab cell:

!pip install -r requirements.txt

Set the Groq key:

import os
os.environ["GROQ_API_KEY"] = "your_groq_api_key"

If using a public PDF URL:

os.environ["CYBER_LAW_PDF_URL"] = "https://your-public-host/cyber-law.pdf"

Start Streamlit:

!streamlit run app.py &>/content/streamlit.log &

Then expose the Streamlit port with your preferred Colab tunneling method.

The first run may take longer because the Sentence Transformer model has to be downloaded.

7. Run on Streamlit Cloud

Create a GitHub repository.

Add:

app.py
requirements.txt
README.md

Deploy the repository on Streamlit Community Cloud.

Add these secrets:

GROQ_API_KEY = "your_groq_api_key"
CYBER_LAW_PDF_URL = "https://your-public-host/cyber-law.pdf"
GROQ_MODEL = "openai/gpt-oss-120b"

Deploy.

Why use a URL for the PDF?

This keeps the GitHub project limited to the requested three files. The app downloads the PDF during initialization and creates the embeddings/FAISS index automatically.

If you do not want a remote URL, simply upload the PDF in the sidebar after the app starts.

8. UI controls

CyberLawGPT includes several controls:

Technicality level

Simple

Balanced

Technical

Legal/Technical

Response size

Short

Medium

Detailed

Very detailed

Answer language

English

Urdu

Roman Urdu

Retrieved passages

Controls how many semantic-search results are supplied to the LLM.

Practical example

Optionally asks the model to include a short example.

Legal-information caution

Optionally adds a short statement that the output is informational and not a substitute for professional legal advice.

9. RAG safeguards

CyberLawGPT uses explicit grounding instructions.

The model is told to:

Use the retrieved PDF passages as the primary legal source.

Avoid inventing section numbers.

Avoid inventing fines or imprisonment terms.

Avoid inventing procedures or exceptions.

Mention the relevant section/page where supported.

Say when the retrieved PDF does not contain enough information.

Distinguish the Act's wording from a plain-language explanation.

Avoid presenting the output as a case-specific legal opinion.

This is especially important for legal applications.

10. Example questions

Try:

What is unauthorized access under the Act?

What is the punishment for unauthorized copying or transmission of data?

What does the Act say about cyber stalking?

What is spoofing and what punishment is provided?

What does the Act say about malicious code?

What powers does an authorized officer have during search and seizure?

How long can traffic data be retained according to the Act?

What does the Act say about real-time collection of information?

What happens when a cyber offence involves a minor?

11. Technical notes

Embeddings

The app uses:

sentence-transformers/all-MiniLM-L6-v2

This is a lightweight sentence-embedding model suitable for a free Streamlit/Colab setup.

Vector database

FAISS uses normalized embeddings with inner-product similarity.

Because the vectors are normalized, inner product behaves like cosine similarity for retrieval.

LLM

The default model is:

openai/gpt-oss-120b

through the Groq API.

You can change it without editing the application by setting:

GROQ_MODEL = "your_available_groq_model"

12. Free-tier considerations

The application itself is designed to avoid paid vector databases or paid embedding APIs.

However:

Groq API availability and limits can change.

Streamlit Cloud resource limits can change.

The Sentence Transformer model must be downloaded.

The PDF must be accessible through the configured URL if you use URL mode.

Large PDFs require more memory and startup time.

For the supplied 29-page legal document, this architecture is intentionally lightweight.

13. Legal disclaimer

CyberLawGPT is an educational/document-grounded AI application.

It is not a lawyer, does not establish an advocate-client relationship, and should not be relied upon as a substitute for advice from a qualified Pakistani legal professional.

The application intentionally answers from the configured/uploaded PDF. If the PDF does not support an answer, the system should state that limitation rather than fabricate a legal rule.

14. Project structure

CyberLawGPT/
│
├── app.py              # Streamlit UI + PDF processing + embeddings + FAISS + Groq
├── requirements.txt    # Python dependencies
└── README.md           # Setup and deployment instructions
