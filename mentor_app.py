# mentor_app.py

import os
import json
import streamlit as st
from openai import OpenAI

# ── 0) STREAMLIT & OPENAI SETUP ──
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
client      = OpenAI(api_key=OPENAI_KEY)
if not OPENAI_KEY:
    st.error("Missing OPENAI_API_KEY in environment")
    st.stop()

st.set_page_config(page_title="AI Mentor", layout="centered")

# ── 1) AGENDA ──
AGENDA = [
    {
        "title": "Meet Your Mentor",
        "prompt": (
            "Hello! I’m your AI Mentor with decades of entrepreneurship experience.\n\n"
            "**Are you ready to start the meeting?**\n\n"
            "Please type exactly:\n\n"
            "`Yes, let’s start the meeting`"
        )
    },
    {
        "title": "Welcome & Introductions",
        "prompt": (
            "❗️ **Action:** Enter each team member’s full name, one per line.\n\n"
            "Example:\n"
            "```\nAlice Smith\nBob Johnson\nCarol Lee\n```"
        )
    },
    {
        "title": "Problem Statement",
        "prompt": (
            "❗️ **Action:** One-sentence problem statement starting “Our problem is …”\n\n"
            "Example:\n"
            "```\nOur problem is that small businesses struggle to find affordable marketing tools.\n```"
        )
    },
    {
        "title": "Solution Overview",
        "prompt": (
            "❗️ **Action:** One-sentence solution overview starting “Our solution is …”\n\n"
            "Example:\n"
            "```\nOur solution is a mobile app that automates social-media posts for local shops.\n```"
        )
    },
    {
        "title": "Wrap-Up",
        "prompt": "Click **Next** to receive your mentor’s final wrap-up."
    },
]

# ── 2) AUTHENTICATION ──
if "team" not in st.session_state:
    name          = st.text_input("Team name")
    pw            = st.text_input("Password", type="password")
    login_clicked = st.button("Login")         # ← only one button call!
    if login_clicked:
        if pw == "letmein":
            st.session_state.team = name
        else:
            st.error("Invalid credentials")
    st.stop()

team = st.session_state.team
st.title(f"👥 Team {team} — AI Mentor")

# ── 3) PERSISTENCE: LOAD / INIT HISTORY & STEP ──
data_dir     = "data"
os.makedirs(data_dir, exist_ok=True)
history_file = os.path.join(data_dir, f"{team}_history.json")

if "history" not in st.session_state:
    if os.path.exists(history_file):
        st.session_state.history = json.load(open(history_file))
    else:
        st.session_state.history = [
            {
                "role": "system",
                "content": (
                    "You are a wise AI mentor with decades of entrepreneurship experience. "
                    "After each team response, first say “Thanks for the input.” "
                    "Then give an insightful comment, and finally instruct them on what to do next."
                )
            }
        ]

if "step" not in st.session_state:
    st.session_state.step = 0

# ── 4) SIDEBAR AGENDA ──
st.sidebar.title("Agenda")
for idx, item in enumerate(AGENDA):
    marker = "➡️" if idx == st.session_state.step else "  "
    st.sidebar.write(f"{marker} Step {idx+1}: {item['title']}")

# ── 5) MAIN: DISPLAY CURRENT STEP ──
i = st.session_state.step
st.header(f"Step {i+1}: {AGENDA[i]['title']}")
st.write(AGENDA[i]["prompt"])

# ── 6) CAPTURE INPUT & CHAT ──
user_input = st.text_area("Your response here", key=f"resp_{i}")
if st.button("Next"):
    # append the user’s input
    st.session_state.history.append({"role": "user", "content": user_input})

    # call the new OpenAI v1 client
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=st.session_state.history,
        temperature=0.7,
    )
    answer = resp.choices[0].message.content

    # append the mentor’s reply
    st.session_state.history.append({"role": "assistant", "content": answer})

    # persist to disk
    with open(history_file, "w") as f:
        json.dump(st.session_state.history, f, indent=2)

    # advance step
    if st.session_state.step < len(AGENDA) - 1:
        st.session_state.step += 1

# ── 7) RENDER CHAT HISTORY (full session) ──
for msg in st.session_state.history[1:]:
    who = "👤 You:" if msg["role"] == "user" else "🤖 Mentor:"
    st.markdown(f"**{who}** {msg['content']}")
