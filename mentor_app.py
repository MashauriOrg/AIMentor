# mentor_app.py

import os, sys, json, subprocess
import streamlit as st
import faiss
import numpy as np
import openai

# 0) Auto-build on first cold start
if not os.path.exists("faiss_index/index.faiss"):
    subprocess.run([sys.executable, "ingest_books.py"], check=True)

# 1) Define your simple agenda
AGENDA = [
    {"title":"Meet Mentor", "prompt":"Hello! I’m your AI Mentor … any questions?"},
    {"title":"Confirm to Start", "prompt":"Type exactly `Yes, let’s start the meeting`"},
    {"title":"Welcome & Intros","prompt":"❗️ **Action:** Enter each member’s full name, one per line."},
    {"title":"Problem","prompt":"❗️ **Action:** One-sentence problem starting “Our problem is …”"},
    {"title":"Solution","prompt":"❗️ **Action:** One-sentence solution starting “Our solution is …”"},
    {"title":"Wrap-Up","prompt":"Click **Next** to get your final wrap-up."}
]

# 2) Streamlit & OpenAI init
st.set_page_config("AI Mentor", layout="centered")
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    st.error("Missing OPENAI_API_KEY")
    st.stop()

# 3) Load FAISS index + texts
try:
    index = faiss.read_index("faiss_index/index.faiss")
    texts = np.load("faiss_index/texts.npy", allow_pickle=True)
except Exception as e:
    st.error(f"Failed to load FAISS index: {e}")
    st.stop()

# 4) Simple login
if "team" not in st.session_state:
    name = st.text_input("Team name")
    pw   = st.text_input("Password", type="password")
    if st.button("Login") and pw == "letmein":
        st.session_state.team = name
    else:
        if st.button("Login"): st.error("Invalid credentials")
    st.stop()

team = st.session_state.team
st.title(f"👥 Team {team} — AI Mentor")

# 5) Load or init history & step
data_dir = "data"; os.makedirs(data_dir, exist_ok=True)
hist_file = os.path.join(data_dir, f"{team}_history.json")

if "history" not in st.session_state:
    if os.path.exists(hist_file):
        st.session_state.history = json.load(open(hist_file))
    else:
        st.session_state.history = [{"role":"system","content":"You are a Socratic AI mentor."}]

if "step" not in st.session_state:
    st.session_state.step = 0

# 6) Sidebar agenda
st.sidebar.title("Agenda")
for idx, item in enumerate(AGENDA):
    mark = "➡️" if idx == st.session_state.step else ""
    st.sidebar.write(f"{mark} {idx+1}. {item['title']}")

# 7) Show current step
i = st.session_state.step
st.header(f"Step {i+1}: {AGENDA[i]['title']}")
st.write(AGENDA[i]["prompt"])

# 8) Capture answer & advance
if st.button("Next"):
    user_txt = st.text_area("Your response", key=f"resp_{i}")
    # Retrieve relevant book passages (optional RAG)
    emb = openai.Embedding.create(model="text-embedding-ada-002", input=user_txt)
    vec = np.array(emb["data"][0]["embedding"], dtype="float32")[None]
    D,I = index.search(vec, 3)
    context = "\n\n".join(texts[j] for j in I[0])

    # Build chat history
    st.session_state.history.append({"role":"user","content":user_txt})
    st.session_state.history.append({"role":"assistant","content":f"[Context:]\n{context}\n\nAnswer Socratically to: {user_txt}"})

    chat = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=st.session_state.history,
        temperature=0.7
    )
    answer = chat.choices[0].message.content
    st.session_state.history.append({"role":"assistant","content":answer})

    # Persist
    with open(hist_file,"w") as f:
        json.dump(st.session_state.history, f, indent=2)

    # Next step
    if i < len(AGENDA)-1:
        st.session_state.step += 1

# 9) Show chat history (newest first)
for msg in reversed(st.session_state.history[1:]):
    who = "👤 You:" if msg["role"]=="user" else "🤖 Mentor:"
    st.markdown(f"**{who}** {msg['content']}")
