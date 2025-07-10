# ingest_books.py

import os
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 1) Grab your key (make sure you've run `export OPENAI_API_KEY="sk-…”`)
openai_key = os.getenv("OPENAI_API_KEY", "sk-<YOUR_TEST_KEY_HERE>")

# 2) Instantiate the embeddings once
embeddings = OpenAIEmbeddings(openai_api_key=openai_key)

# 3) Load all .txt files
docs = []
for fn in os.listdir("extracted_books"):
    if fn.lower().endswith(".txt"):
        loader = TextLoader(f"extracted_books/{fn}", encoding="utf8")
        docs.extend(loader.load())

# 4) Split into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
chunks = splitter.split_documents(docs)

# 5) Build the FAISS index
vectorstore = FAISS.from_documents(chunks, embeddings)

# 6) Save it locally
# … your existing ingestion logic …

vectorstore.save_local("faiss_index")
print(f"✅ Index built with {len(chunks)} chunks")

import numpy as np
os.makedirs("faiss_index", exist_ok=True)
texts     = [doc.page_content for doc in chunks]
metadatas = [doc.metadata       for doc in chunks]
np.save("faiss_index/texts.npy",     texts,     allow_pickle=True)
np.save("faiss_index/metadatas.npy", metadatas, allow_pickle=True)
print(f"✅ Also saved texts.npy & metadatas.npy ({len(texts)} items)")

