"""
knowledge.py — Member A (The Knowledge Keeper / RAG Core)
Contract:  get_answer(question: str) -> str

100% FREE STACK:
  - LLM        : Groq (free, no credit card) -> llama-3.1-8b-instant
  - Embeddings : HuggingFace, runs locally on your machine (no key, free)
  - Index      : FAISS (local, free)

Build order:
  1. Load pmkisan.md
  2. Chunk it
  3. Embed locally + store in FAISS
  4. On each question: retrieve top chunks, answer ONLY from them
"""

import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

# --- Paste your FREE Groq key here (from https://console.groq.com) ---
# Or set it in your terminal:  set GROQ_API_KEY=gsk_your_key_here
# os.environ["GROQ_API_KEY"] = "gsk_..."

_DB = None          # FAISS index, built once
_LLM = None         # the chat model, built once


def _build_index():
    """Read the document, chunk it, embed it locally, store in FAISS. Runs once."""
    global _DB, _LLM

    with open("pmkisan.md", "r", encoding="utf-8") as f:
        text = f.read()

    chunks = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    ).split_text(text)

    # Free local embeddings - downloads a small model the first time (~80MB)
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    _DB = FAISS.from_texts(chunks, embeddings)

    # Free, fast hosted LLM
    _LLM = ChatGroq(model="llama-3.1-8b-instant", temperature=0)


# Phrases that mean "do I personally qualify?" — these can't be answered from
# the document, so we guide the user to the eligibility checker instead.
_ELIGIBILITY_HINTS = [
    "eligible", "qualify", "should i apply", "do i get", "can i apply", "am i able"
]


def get_answer(question: str) -> str:
    """THE CONTRACT FUNCTION. Takes a question, returns a grounded answer."""
    global _DB, _LLM

    if _DB is None:                 # lazy build on first call
        _build_index()

    # Personal-eligibility questions -> redirect to the eligibility tool.
    q_low = question.lower()
    if any(h in q_low for h in _ELIGIBILITY_HINTS):
        return ("It sounds like you want to know if you personally qualify. "
                "Tap the \"Check my eligibility\" button below and I'll ask you "
                "a few quick questions to find out. 😊")

    docs = _DB.similarity_search(question, k=3)
    context = "\n\n".join(d.page_content for d in docs)

    prompt = f"""You are a warm, helpful assistant for three Indian government
schemes: PM-KISAN, the PM Scholarship Scheme (PMSS), and Ayushman Bharat PM-JAY.
Answer the question using ONLY the context below, in a friendly and clear way.
If the answer is NOT in the context, do not invent anything. Instead reply:
"I can help with what each scheme is, who is eligible, the documents needed, and
how to apply. Could you try asking about one of those?"
Keep answers concise and easy to read.

Context:
{context}

Question: {question}
Answer:"""

    return _LLM.invoke(prompt).content


# --- Quick local test: python knowledge.py ---
if __name__ == "__main__":
    questions = [
        "What is PM-KISAN?",
        "What documents do I need for PM-KISAN?",
        "What is the PM Scholarship Scheme?",
        "Who is eligible for the PM Scholarship Scheme?",
        "What is Ayushman Bharat PM-JAY?",
        "How much does PM-JAY cover?",
        "How do I apply for Ayushman Bharat?",
        "What is the weather today?",   # off-topic -> should refuse
    ]
    for q in questions:
        print("Q:", q)
        print("A:", get_answer(q))
        print("-" * 50)
