# ingest_books.py

import os
import sys
import faiss
import numpy as np
import openai
from glob import glob
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 0) Ensure API key
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    print("❌ Missing OPENAI_API_KEY", file=sys.stderr)
    sys.exit(1)

# 1) Load all .txts
files = glob("extracted_books/*.txt")
if not files:
    print("⚠️ No .txt files in extracted_books/", file=sys.stderr)

raw_texts = []
for path in files:
    with open(path, encoding="utf8") as f:
        raw_texts.append(f.read())

# 2) Chunk
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
# wrap as simple objects:
class Doc: 
    def __init__(self, txt): self.page_content = txt
docs = [Doc(t) for t in raw_texts]
chunks = splitter.split_documents(docs)

# 3) Embed each chunk with OpenAI
embeddings = []
for chunk in chunks:
    resp = openai.Embedding.create(model="text-embedding-ada-002",
                                   input=chunk.page_content)
    embeddings.append(np.array(resp["data"][0]["embedding"], dtype="float32"))

matrix = np.stack(embeddings)

# 4) Build & save FAISS index
dim = matrix.shape[1]
index = faiss.IndexFlatL2(dim)
index.add(matrix)
os.makedirs("faiss_index", exist_ok=True)
faiss.write_index(index, "faiss_index/index.faiss")

# 5) Save texts
texts = [c.page_content for c in chunks]
np.save("faiss_index/texts.npy", np.array(texts, dtype=object))

print(f"✅ Built index with {len(chunks)} chunks")
