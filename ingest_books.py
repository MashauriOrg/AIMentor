# ingest_books.py

import os
import sys
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS

# ── Ensure the API key is available ──
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    print("❌ Error: OPENAI_API_KEY environment variable not set.", file=sys.stderr)
    sys.exit(1)

# ── 1) Load all .txts in extracted_books/ ──
docs = []
books_dir = "extracted_books"
if not os.path.isdir(books_dir):
    print(f"❌ Error: Directory '{books_dir}' not found.", file=sys.stderr)
    sys.exit(1)

for fn in os.listdir(books_dir):
    if fn.lower().endswith(".txt"):
        path = os.path.join(books_dir, fn)
        loader = TextLoader(path, encoding="utf8")
        docs.extend(loader.load())

if not docs:
    print(f"⚠️ Warning: No .txt files loaded from '{books_dir}'.", file=sys.stderr)

# ── 2) Split into manageable chunks & embed ──
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks   = splitter.split_documents(docs)

embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
vectorstore = FAISS.from_documents(chunks, embeddings)

# ── 3) Save the index locally ──
index_dir = "faiss_index"
os.makedirs(index_dir, exist_ok=True)
vectorstore.save_local(index_dir)

print(f"✅ Index built with {len(chunks)} chunks and saved to '{index_dir}/'.")
