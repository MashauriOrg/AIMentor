# mentor_app.py

import os
import streamlit as st
from openai import OpenAI
import faiss
import numpy as np
from langchain_community.embeddings import OpenAIEmbeddings


# — CONFIG —
# — CONFIG & CLIENT —
api_key = os.getenv("OPENAI_API_KEY")
client  = OpenAI(api_key=api_key)


st.set_page_config(page_title="AI Mentor", layout="centered")

# — LOAD FAISS INDEX & TEXTS —
# We assume ingest_books.py produced "faiss_index" + "texts.npy" + "metadatas.npy"
index = faiss.read_index("faiss_index/index.faiss")
texts     = np.load("faiss_index/texts.npy", allow_pickle=True)
metadatas = np.load("faiss_index/metadatas.npy", allow_pickle=True)

# — AUTH/GATEKEEP —
# --- Team login ---
if "team" not in st.session_state:
    team = st.text_input("Team name", key="team_name")
    pw   = st.text_input("Password", type="password", key="team_pw")
    if st.button("Login"):
        if pw == "letmein":
            st.session_state.team = team
        else:
            st.error("Invalid credentials")
    # Don’t run the rest of the app until logged in
    if "team" not in st.session_state:
        st.stop()


st.title(f"👥 Team {st.session_state.team} — Your AI Mentor")

# — CHAT STATE —
if "history" not in st.session_state:
    st.session_state.history = [
        {"role": "system", "content": (
            "You are a wise mentor with decades of entrepreneurship experience. "
            "You use a Socratic style, drawing on a library of startup books."
        )}
    ]

# — USER INPUT —
query = st.text_input("Ask your mentor…")
if st.button("Send") and query:
    # 1) Embed the question
    emb_model = OpenAIEmbeddings(openai_api_key=api_key)

    q_emb     = emb_model.embed_query(query)

    # 2) FAISS search top 3
    D, I = index.search(np.array([q_emb], dtype="float32"), 3)
    context = "\n\n".join(texts[i] for i in I[0])

    # 3) Build messages
    st.session_state.history.append({"role": "user", "content": query})
    st.session_state.history.append(
        {"role": "assistant", "content": (
            f"[Context from books:]\n{context}\n\n"
            f"Answer Socratically to: {query}"
        )}
    )

# 4) Call OpenAI via the new client
resp = client.chat.completions.create(
    model="gpt-4o",
    messages=st.session_state.history,
    temperature=0.7
)
answer = resp.choices[0].message.content

# 5) Record & show
st.session_state.history[-1]["content"] = answer

# — RENDER HISTORY —
for msg in st.session_state.history[1:]:
    prefix = "👤 You:" if msg["role"]=="user" else "🤖 Mentor:"
    st.markdown(f"**{prefix}** {msg['content']}")
