# mentor_app.py

import os
import json
import streamlit as st
from openai import OpenAI

# ── STREAMLIT & OPENAI SETUP ──
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_KEY)
if not OPENAI_KEY:
    st.error("Missing OPENAI_API_KEY in environment")
    st.stop()

st.set_page_config(page_title="AI Mentor", layout="centered")

# ── AGENDA ──
AGENDA = [
    {"title": "Meet Your Mentor",
     "prompt": (
         "Hello! I’m your AI Mentor with decades of entrepreneurship experience and really wantto help you successfully develop your venture idea.\n\n"
         "**Capabilities:** I ask Socratic questions and draw on a curated book library.\n\n"
         "**Limitations:** I generally start looking for information from the top best practioce startup books in the world before I answer questions.I also remember what you tell me.\n\n"
         "**Limitations 2:** I may have lots of information but am still taking baby steps to learn how to communicate with you, so please be patient with me.\n\n"
         "❓  Please type any questions you have for me now."
     )},
    {"title": "Confirm to Start",
     "prompt": (
         "When you’re ready, **type exactly**:\n\n"
         "`Yes, let’s start the meeting`"
     )},
    {"title": "Welcome & Introductions",
     "prompt": (
         "❗️ **Action:** Enter each team member’s full name, one per line."
     )},
    {"title": "Problem Statement",
     "prompt": (
         "❗️ **Action:** One-sentence problem starting “Our problem is …”"
     )},
    {"title": "Solution Overview",
     "prompt": (
         "❗️ **Action:** One-sentence solution starting “Our solution is …”"
     )},
    {"title": "Wrap-Up",
     "prompt": (
         "Click **Next** to receive your mentor’s final wrap-up."
     )}
]

# ── AUTHENTICATION ──
if "team" not in st.session_state:
    name = st.text_input("Team name")
    pw   = st.text_input("Password", type="password")
    login_clicked = st.button("Login")  # only one button call
    if login_clicked:
        if pw == "letmein":
            st.session_state.team = name
        else:
            st.error("Invalid credentials")
    st.stop()

team = st.session_state.team
st.title(f"👥 Team {team} — AI Mentor")

# ── PERSISTENCE: HISTORY & STEP ──
data_dir = "data"
os.makedirs(data_dir, exist_ok=True)
history_file = os.path.join(data_dir, f"{team}_history.json")

if "history" not in st.session_state:
    if os.path.exists(history_file):
        st.session_state.history = json.load(open(history_file, "r"))
    else:
        st.session_state.history = [
            {"role": "system", "content":
                "You are a wise AI mentor. You ask Socratic questions and draw on a curated library of entrepreneurship books."
            }
        ]
# RIGHT HERE, record the number of “old” messages:
if "start_index" not in st.session_state:
    st.session_state.start_index = len(st.session_state.history)


if "step" not in st.session_state:
    st.session_state.step = 0

# ── SIDEBAR: AGENDA ──
st.sidebar.title("Agenda")
for idx, item in enumerate(AGENDA):
    marker = "➡️" if idx == st.session_state.step else ""
    st.sidebar.write(f"{marker} {idx+1}. {item['title']}")

# ── MAIN: CURRENT STEP ──
i = st.session_state.step
st.header(f"Step {i+1}: {AGENDA[i]['title']}")
st.write(AGENDA[i]["prompt"])

# ── INPUT & OPENAI CHAT ──
user_input = st.text_area("Your response here", key=f"resp_{i}")
if st.button("Next"):
    # 1) Append user message
    st.session_state.history.append({"role": "user", "content": user_input})

    # 2) Call new OpenAI client
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=st.session_state.history,
        temperature=0.7,
    )
    answer = resp.choices[0].message.content

    # 3) Append assistant message
    st.session_state.history.append({"role": "assistant", "content": answer})

    # 4) Persist full history
    with open(history_file, "w") as f:
        json.dump(st.session_state.history, f, indent=2)

    # 5) Advance step and rerun to reset widgets
    if st.session_state.step < len(AGENDA) - 1:
        st.session_state.step += 1
   

# ── RENDER HISTORY (NEWEST FIRST) ──
for msg in reversed(st.session_state.history[st.session_state.start_index:]):
    prefix = "👤 You:" if msg["role"]=="user" else "🤖 Mentor:"
    st.markdown(f"**{prefix}** {msg['content']}")
