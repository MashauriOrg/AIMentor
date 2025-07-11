# ingest_books.py

import os
import sys
import faiss
import numpy as np
import openai
from glob import glob

# 0) Load API key
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    print("❌ Missing OPENAI_API_KEY", file=sys.stderr)
    sys.exit(1)

# 1) Read all .txt files
texts = []
for path in glob("extracted_books/*.txt"):
    with open(path, encoding="utf8") as f:
        texts.append(f.read())
if not texts:
    print("⚠️ No .txt in extracted_books/", file=sys.stderr)

# 2) Simple 1 000-char chunking
chunks = []
for doc in texts:
    for i in range(0, len(doc), 1000):
        chunks.append(doc[i : i + 1000])

# 3) Embed via OpenAI
vectors = []
for chunk in chunks:
    resp = openai.Embedding.create(model="text-embedding-ada-002", input=chunk)
    vectors.append(np.array(resp["data"][0]["embedding"], dtype="float32"))

if not vectors:
    print("❌ No embeddings generated; check your API key and texts.", file=sys.stderr)
    sys.exit(1)

matrix = np.stack(vectors)  # shape (num_chunks, dim)

# 4) Build and save FAISS index
dim = matrix.shape[1]
index = faiss.IndexFlatL2(dim)
index.add(matrix)
os.makedirs("faiss_index", exist_ok=True)
faiss.write_index(index, "faiss_index/index.faiss")

# 5) Save the raw chunk texts
np.save("faiss_index/texts.npy", np.array(chunks, dtype=object))

print(f"✅ Built FAISS index with {len(chunks)} chunks.")
