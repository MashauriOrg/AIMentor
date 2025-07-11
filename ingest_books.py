# ingest_books.py

import os
import sys
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS

# ── 0) Ensure the API key is set ──
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    print("❌ Error: Missing OPENAI_API_KEY", file=sys.stderr)
    sys.exit(1)

# ── 1) Load all .txt files from extracted_books/ ──
books_dir = "extracted_books"
if not os.path.isdir(books_dir):
    print(f"❌ Error: Directory '{books_dir}' not found.", file=sys.stderr)
    sys.exit(1)

docs = []
for filename in os.listdir(books_dir):
    if filename.lower().endswith(".txt"):
        path = os.path.join(books_dir, filename)
        loader = TextLoader(path, encoding="utf8")
        docs.extend(loader.load())

if not docs:
    print(f"⚠️ Warning: No .txt files found in '{books_dir}'.", file=sys.stderr)

# ── 2) Chunk & embed ──
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks   = splitter.split_documents(docs)

emb = OpenAIEmbeddings(openai_api_key=openai_key)
vectorstore = FAISS.from_documents(chunks, emb)

# ── 3) Save the index ──
index_dir = "faiss_index"
os.makedirs(index_dir, exist_ok=True)
vectorstore.save_local(index_dir)

print(f"✅ Index built with {len(chunks)} chunks and saved to '{index_dir}/'.")
