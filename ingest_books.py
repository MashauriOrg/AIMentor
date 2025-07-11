# ingest_books.py

import os

# --- Imports with fallback for embeddings, loaders, and FAISS ---  
try:
    from langchain_community.embeddings import OpenAIEmbeddings
except ImportError:
    from langchain.embeddings.openai import OpenAIEmbeddings

try:
    from langchain_community.document_loaders import TextLoader
except ImportError:
    from langchain.document_loaders import TextLoader

try:
    from langchain_community.vectorstores import FAISS
except ImportError:
    from langchain.vectorstores import FAISS

from langchain.text_splitter import RecursiveCharacterTextSplitter

# --- Make sure OPENAI_API_KEY is set ---
import os
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    raise ValueError("Missing OPENAI_API_KEY")

# 1. Load all .txt in extracted_books/
docs = []
for fn in os.listdir("extracted_books"):
    if fn.endswith(".txt"):
        loader = TextLoader(f"extracted_books/{fn}", encoding="utf8")
        docs.extend(loader.load())

# 2. Split & embed
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks   = splitter.split_documents(docs)
emb      = OpenAIEmbeddings(openai_api_key=openai_key)
vectorstore = FAISS.from_documents(chunks, emb)

# 3. Save index
vectorstore.save_local("faiss_index")
print("✅ Index built with", len(chunks), "chunks")
