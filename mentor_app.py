# mentor_app.py

import os
import json
import streamlit as st
from openai import OpenAI

# ── STREAMLIT & OPENAI SETUP ──
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
client     = OpenAI(api_key=OPENAI_KEY)
if not OPENAI_KEY:
    st.error("Missing OPENAI_API_KEY")
    st.stop()

st.set_page_config(page_title="AI Mentor", layout="centered")

# ── AGENDA ──
AGENDA = [
    {
        "title": "Meet Your Mentor",
        "prompt": (
            "Hello! I’m your AI Mentor with decades of entrepreneurship experience—ready to help you develop your venture.\n\n"
            "**Capabilities:** I ask Socratic questions and draw on a curated book library.\n\n"
            "**Limitations:** I start by reviewing top-practice startup books before I answer questions, and I remember what you tell me.\n\n"
            "**Communication:** Our chats appear below; next steps appear above the input.\n\n"
            "**Are you ready to start the meeting?**\n\n"
            "Please type exactly:\n\n"
            "`Yes`"
        )
    },
    {
        "title": "Welcome & Introductions",
        "prompt": (
            "❗️ **Action:** Enter each team member’s full name, one per line.\n\n"
            "Example:\n```\nAlice Smith\nBob Johnson\nCarol Lee\n```"
        )
    },
    {
        "title": "Problem Statement",
        "prompt": (
            "❗️ **Action:** Provide a one-sentence problem starting “Our problem is …”.\n\n"
            "Example:\n```\nOur problem is that small businesses struggle to find affordable marketing tools.\n```"
        )
    },
    {
        "title": "Solution Overview",
        "prompt": (
            "❗️ **Action:** Provide a one-sentence solution starting “Our solution is …”.\n\n"
            "Example:\n```\nOur solution is a mobile app that automates social-media posts for local shops.\n```"
        )
    },
    {
        "title": "Wrap-Up",
        "prompt": "Click **Next** to receive your mentor’s final wrap-up."
    },
]

# ── AUTHENTICATION ──
if "team" not in st.session_state:
    name          = st.text_input("Team name")
    pw            = st.text_input("Password", type="password")
    login_clicked = st.button("Login")
    if login_clicked:
        if pw == "letmein":
            st.session_state.team = name
        else:
            st.error("Invalid credentials")
    st.stop()

team = st.session_state.team
st.title(f"👥 Team {team} — AI Mentor")

# ── PERSISTENCE: HISTORY & STEP ──
data_dir     = "data"
os.makedirs(data_dir, exist_ok=True)
history_file = os.path.join(data_dir, f"{team}_history.json")

if "history" not in st.session_state:
    if os.path.exists(history_file):
        st.session_state.history = json.load(open(history_file, "r"))
    else:
        st.session_state.history = [
            {
                "role": "system",
                "content": (
                    "You are a wise AI mentor with decades of entrepreneurship experience. "
                    "After each team response, first say “Thanks for the input.” "
                    "Then add an insightful comment, and finally instruct them on what to do next."
                )
            }
        ]

# remember where “old” messages end so we only render the new
if "start_index" not in st.session_state:
    st.session_state.start_index = len(st.session_state.history)

if "step" not in st.session_state:
    st.session_state.step = 0

# ── SIDEBAR: Agenda Navigation ──
st.sidebar.title("Agenda")
for idx, item in enumerate(AGENDA):
    marker = "➡️" if idx == st.session_state.step else ""
    st.sidebar.write(f"{marker} Step {idx+1}: {item['title']}")

# ── MAIN VIEW: Current Step ──
i = st.session_state.step
st.header(f"Step {i+1}: {AGENDA[i]['title']}")
st.write(AGENDA[i]["prompt"])

# ── INPUT & CHAT LOGIC ──
user_input = st.text_area("Your response here", key=f"resp_{i}")
if st.button("Next"):

    # --- Step 0: yes/no gate (no LLM call) ---
    if i == 0:
        if user_input.strip().lower() == "yes":
            st.session_state.step = 1
        else:
            reminder = (
                "Are you sure you do not want to start the meeting now?\n\n"
                "Please type **Yes** to begin or **No** if you want to delay."
            )
            st.session_state.history.append({"role": "assistant", "content": reminder})
            with open(history_file, "w") as f:
                json.dump(st.session_state.history, f, indent=2)

    # --- Steps 1+ : real chat flow ---
    elif i > 0:
        # 1) log the user’s input
        st.session_state.history.append({"role": "user", "content": user_input})

        # 2) call the LLM
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=st.session_state.history,
            temperature=0.7,
        )
        answer = resp.choices[0].message.content

        # 3) log the mentor’s reply
        st.session_state.history.append({"role": "assistant", "content": answer})

        # 4) save to disk
        with open(history_file, "w") as f:
            json.dump(st.session_state.history, f, indent=2)

        # 5) advance to next step
        if st.session_state.step < len(AGENDA) - 1:
            st.session_state.step += 1

# ── RENDER ONLY THIS SESSION’S CHAT ──
for msg in st.session_state.history[st.session_state.start_index:]:
    who = "👤 You:" if msg["role"] == "user" else "🤖 Mentor:"
    st.markdown(f"**{who}** {msg['content']}")
