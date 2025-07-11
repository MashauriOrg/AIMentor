# ingest_books.py

import os
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS

# — Ensure your API key is set —
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    raise ValueError("Missing OPENAI_API_KEY")

# 1) Load all .txt files in extracted_books/
docs = []
for fn in os.listdir("extracted_books"):
    if fn.endswith(".txt"):
        loader = TextLoader(os.path.join("extracted_books", fn), encoding="utf8")
        docs.extend(loader.load())

# 2) Split into ~1 000-char chunks with 200-char overlap
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(docs)

# 3) Embed and build FAISS index
emb = OpenAIEmbeddings(openai_api_key=openai_key)
vectorstore = FAISS.from_documents(chunks, emb)

# 4) Save to disk
vectorstore.save_local("faiss_index")
print(f"✅ Index built with {len(chunks)} chunks")
