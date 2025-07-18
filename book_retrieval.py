import os
import numpy as np
import faiss
from openai import OpenAI

# ─── Configuration for FAISS index path ────────────────────────────────────────
# On Render, FAISS_INDEX_PATH will be set to '/mnt/data/faiss_index/index.faiss'.
# Locally, it falls back to './faiss_index/index.faiss' in your repo.
INDEX_PATH = os.getenv(
    "FAISS_INDEX_PATH",
    os.path.join(os.path.dirname(__file__), "faiss_index", "index.faiss"),
)

_index = None
_texts = None
_client = None

def _load_resources():
    global _index, _texts, _client
    if _index is None or _texts is None:
        # Read the FAISS index from wherever INDEX_PATH points
        _index = faiss.read_index(INDEX_PATH)
        # Texts remain in the repo; no change needed here
        _texts = np.load(
            os.path.join(os.path.dirname(__file__), "faiss_index", "texts.npy"),
            allow_pickle=True
        )
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _index, _texts, _client

def search_books(query: str, top_k: int = 3) -> list[str]:
    """Return top book excerpts relevant to the query."""
    index, texts, client = _load_resources()
    resp = client.embeddings.create(model="text-embedding-ada-002", input=query)
    vector = np.array(resp.data[0].embedding, dtype="float32").reshape(1, -1)
    distances, indices = index.search(vector, top_k)
    results = [texts[i] for i in indices[0] if i != -1]
    return results
