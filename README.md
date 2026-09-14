⚖️ CyberLawGPT

CyberLawGPT is a RAG-based Pakistani cyber-law information assistant built with:

Python

Streamlit

FAISS

Sentence Transformers

Groq API

openai/gpt-oss-120b

Important design choice

CyberLawGPT does not require the PECA PDF to be uploaded by the user.

The supplied Prevention of Electronic Crimes Act, 2016 (PECA 2016) was studied and its relevant legal concepts were structured into the application's built-in legal knowledge base.

At startup, CyberLawGPT:

Built-in PECA legal knowledge
          ↓
Sentence Transformer embeddings
          ↓
FAISS vector index
          ↓
User question
          ↓
Relevant legal passages
          ↓
Groq + openai/gpt-oss-120b
          ↓
Answer

The original PDF is therefore not a runtime dependency.

Features

Legal RAG

Questions are converted into embeddings and matched against the built-in PECA knowledge using FAISS.

Technicality control

Users can choose:

Simple

Balanced

Technical

Legal / Technical

Response size

Users can choose:

Short

Medium

Detailed

Very detailed

Language

Users can choose:

English

Urdu

Roman Urdu

Additional controls

Number of retrieved legal passages

Practical example on/off

Legal-information caution on/off

Retrieved legal material viewer

Chat history during the current session

PECA knowledge covered

The built-in knowledge is structured around material from the supplied PECA 2016 document, including:

Definitions

Unauthorized access

Unauthorized interception

Unauthorized copying/transmission

Interference with or damage to information systems/data

Unauthorized access involving critical infrastructure

Electronic crimes and punishments as described in the Act

Hacking / illegal access

Denial-of-service and distributed denial-of-service concepts mentioned in the Act's objects

Electronic forgery and fraud

Cyber terrorism

Malicious code

Identity theft

Prosecution and trial

Cognizance

Bailability

Compoundability

Compensation

Investigation and forensic procedures

Relation with other laws

Rule making

Legal grounding rule

The application instructs the LLM not to invent missing legal details.

For example, if the built-in material does not contain a precise punishment, the model is told to say that the available material does not provide that detail instead of guessing.

This is important because a legal RAG application should distinguish between:

What the Act explicitly states.

What is only mentioned in the Act's Statement of Objects and Reasons.

Information that is not available in the application's knowledge base.

1. Get a Groq API key

Create an API key from Groq.

Do not put the API key directly inside app.py.

Set:

GROQ_API_KEY=your_api_key_here

Optional model variable:

GROQ_MODEL=openai/gpt-oss-120b

The application already defaults to:

openai/gpt-oss-120b

2. Run locally

Create the project:

CyberLawGPT/
├── app.py
├── requirements.txt
└── README.md

Install dependencies:

pip install -r requirements.txt

Set your API key.

Windows PowerShell:

$env:GROQ_API_KEY="your_api_key_here"

Linux/macOS:

export GROQ_API_KEY="your_api_key_here"

Run:

streamlit run app.py

3. Run on Google Colab

Upload the three files to Colab or clone your GitHub repository.

Install dependencies:

!pip install -r requirements.txt

Set the API key:

import os
os.environ["GROQ_API_KEY"] = "your_api_key_here"

Run Streamlit:

!streamlit run app.py &>/content/logs.txt &

For a public Colab demo, use a suitable tunnel such as Cloudflare Tunnel or another tunnel service.

4. Deploy on Streamlit Cloud

Push:

app.py
requirements.txt
README.md

to GitHub.

In Streamlit Cloud, add the secret:

GROQ_API_KEY = "your_api_key_here"
GROQ_MODEL = "openai/gpt-oss-120b"

Then deploy app.py.

No PDF upload or PDF URL is required.

Why FAISS is used

FAISS provides vector similarity search.

The application's legal passages are embedded using:

sentence-transformers/all-MiniLM-L6-v2

The embeddings are stored in a FAISS IndexFlatIP index.

When a user asks a question:

Question
   ↓
Question embedding
   ↓
FAISS similarity search
   ↓
Relevant PECA passages
   ↓
Groq
   ↓
Answer

This reduces the chance that the language model answers from unrelated general knowledge.

Environment variables

Variable

Required

Default

GROQ_API_KEY

Yes

None

GROQ_MODEL

No

openai/gpt-oss-120b

Example questions

Try:

What is unauthorized access under PECA?

What does PECA say about unauthorized copying of data?

What is critical infrastructure in the context of PECA?

Does PECA address denial-of-service attacks?

What cybercrime categories are mentioned in the Statement of Objects and Reasons?

What provisions deal with prosecution and trial?

Limitations

This application is intentionally grounded in the supplied PECA 2016 material.

It should not be treated as a complete database of every Pakistani cyber-related statute, amendment, regulation, notification, or court judgment.

If a question requires information that is absent from the built-in knowledge base, CyberLawGPT should say so rather than fabricate an answer.

Laws can also change. For a real legal matter, verify the current law and consult a qualified Pakistani legal professional.

Project structure

Only three project files are required:

app.py
requirements.txt
README.md

The PECA PDF is not bundled with the project and is not required at runtime.

License / legal notice

This project is an educational legal-information application.

CyberLawGPT is not a law firm, does not create an advocate-client relationship, and does not replace professional legal advice.
