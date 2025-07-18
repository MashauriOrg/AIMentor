import os
import numpy as np
import faiss
from openai import OpenAI

_index = None
_texts = None
_client = None


def _load_resources():
    global _index, _texts, _client
    if _index is None or _texts is None:
        _index = faiss.read_index("faiss_index/index.faiss")
        _texts = np.load("faiss_index/texts.npy", allow_pickle=True)
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
