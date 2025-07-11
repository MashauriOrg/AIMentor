# mentor_app.py

import os
import json
import subprocess
import streamlit as st
import faiss
import numpy as np
import openai

# 0) Auto-ingest on first start
if not os.path.exists("faiss_index/index.faiss"):
    subprocess.run(["python", "ingest_books.py"], check=True)

# 1) Agenda definitions
INTRO_STEPS = [
    {
        "title": "Meet Your Mentor",
        "prompt": (
            "Hello! I’m your AI Mentor with decades of entrepreneurship experience.\n\n"
            "**Capabilities:**\n"
            "- I’ll guide you step-by-step\n"
            "- I’ll ask Socratic questions based on our book library\n\n"
            "**Limitations:**\n"
            "- I only know what’s in these books and what you tell me\n\n"
            "❓ Type any questions for me now."
        )
    },
    {
        "title": "Confirm to Start",
        "prompt": (
            "When you’re ready, **type exactly**:\n\n"
            "`Yes, let’s start the meeting`"
        )
    },
    {
        "title": "Agenda Overview",
        "prompt": (
            "Here’s our 9-step agenda:\n"
            "1. Welcome & Introductions\n"
            "2. Problem Statement\n"
            "…\n"
            "9. Wrap-Up\n\n"
            "Click **Next** to begin Step 1."
        )
    }
]

MEETING_STEPS = [
    {
        "title": "Welcome & Introductions",
        "prompt": (
            "❗️ **Action:** Enter each team member’s full name, one per line.\n\n"
            "Example:\nAlice Smith\nBob Johnson"
        )
    },
    {
        "title": "Problem Statement",
        "prompt": "❗️ **Action:** One-sentence problem starting “Our problem is …”"
    },
    {
        "title": "Solution Overview",
        "prompt": "❗️ **Action:** One-sentence solution starting “Our solution is …”"
    },
    # … add the other steps similarly …
    {
        "title": "Wrap-Up",
        "prompt": "📝 Click **Next** to receive my final wrap-up."
    }
]

AGENDA = INTRO_STEPS + MEETING_STEPS

# 2) Streamlit setup
openai.api_key = os.getenv("OPENAI_API_KEY")
st.set_page_config(page_title="AI Mentor", layout="centered")

# 3) Load FAISS & texts
index = faiss.read_index("faiss_index/index.faiss")
texts = np.load("faiss_index/texts.npy", allow_pickle=True)

# 4) Auth
if "team" not in st.session_state:
    name = st.text_input("Team name")
    pw   = st.text_input("Password", type="password")
    if st.button("Login") and pw == "letmein":
        st.session_state.team = name
    else:
        if st.button("Login"): st.error("Invalid")
    st.stop()

# 5) Init history & step
team = st.session_state.team
data_dir = "data"; os.makedirs(data_dir, exist_ok=True)
hist_file = f"{data_dir}/{team}_history.json"

if "history" not in st.session_state:
    if os.path.exists(hist_file):
        st.session_state.history = json.load(open(hist_file))
    else:
        st.session_state.history = [
            {"role":"system","content":"You are a Socratic AI mentor."}
        ]
if "step" not in st.session_state: st.session_state.step = 0

# 6) Sidebar agenda
st.sidebar.title("Agenda")
for i, item in enumerate(AGENDA):
    mark = "➡️" if i==st.session_state.step else ""
    st.sidebar.write(f"{mark} {i+1}. {item['title']}")

# 7) Show current step
i = st.session_state.step
st.header(f"Step {i+1}: {AGENDA[i]['title']}")
st.write(AGENDA[i]["prompt"])

# 8) Input & advance
resp = None
if st.button("Next"):
    # record user input
    user_txt = st.text_area("Your response", key=f"resp_{i}")
    st.session_state.history.append({"role":"user","content":user_txt})

    # optional RAG retrieval:
    # vec = openai.Embedding.create(model="text-embedding-ada-002",input=user_txt)
    # D,I = index.search(np.array(vec["data"][0]["embedding"],dtype="float32")[None],3)
    # context = "\n\n".join(texts[j] for j in I[0])
    # prompt = f"{context}\n\nUser: {user_txt}"

    # call chat
    chat = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=st.session_state.history,
        temperature=0.7
    )
    resp = chat.choices[0].message.content
    st.session_state.history.append({"role":"assistant","content":resp})

    # persist
    with open(hist_file,"w") as f:
        json.dump(st.session_state.history, f, indent=2)

    # advance step
    if st.session_state.step < len(AGENDA)-1:
        st.session_state.step += 1

# 9) Show history (newest first)
for msg in reversed(st.session_state.history[1:]):
    who = "👤 You:" if msg["role"]=="user" else "🤖 Mentor:"
    st.write(f"**{who}** {msg['content']}")
