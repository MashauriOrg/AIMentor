import os
import json
import streamlit as st
from openai import OpenAI

# ── STREAMLIT & OPENAI SETUP ──
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("Missing OPENAI_API_KEY environment variable")
    st.stop()
client = OpenAI(api_key=api_key)

st.set_page_config(page_title="AI Mentor", layout="centered")

# ── AGENDA DEFINITIONS ──
# mentor_app.py

import os
import json
import streamlit as st
from openai import OpenAI

# ── STREAMLIT & OPENAI SETUP ──
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
client      = OpenAI(api_key=OPENAI_KEY)
if not OPENAI_KEY:
    st.error("Missing OPENAI_API_KEY")
    st.stop()

st.set_page_config(page_title="AI Mentor", layout="centered")

# ── AGENDA ──
AGENDA = [
    {
        "title": "Meet Your Mentor",
        "prompt": (
            "Hello! I’m your AI Mentor with decades of entrepreneurship experience and really want to help you successfully develop your venture idea.\n\n"
            "**Capabilities:** I ask Socratic questions and draw on a curated book library.\n\n"
            "**Limitations:** I generally start looking for information from the top best practice startup books in the world before I answer questions. I also remember what you tell me.\n\n"
            "**Limitations 2:** I may have lots of information but am still taking baby steps to learn how to communicate with you, so please be patient with me.\n\n"
            "**Communication:** Our chats are captured below the input area and the things you need to do next are found here, above the input area.\n\n"
            "❓  **Please type any questions you have for me now.**"
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
    name = st.text_input("Team name")
    pw = st.text_input("Password", type="password")
    if st.button("Login"):
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
        with open(history_file, "r") as f:
            st.session_state.history = json.load(f)
    else:
        st.session_state.history = [
            {"role": "system", "content": (
                "You are a wise AI mentor with decades of entrepreneurship experience. "
                "After each team input, say 'Thanks for the input.' then provide guidance."
            )}
        ]
    st.session_state.start_index = len(st.session_state.history)

if "step" not in st.session_state:
    st.session_state.step = 0

# ── SIDEBAR AGENDA ──
st.sidebar.title("Meeting Agenda")
for idx, item in enumerate(AGENDA):
    marker = "➡️" if idx == st.session_state.step else "  "
    st.sidebar.write(f"{marker} Step {idx+1}: {item['title']}")

# ── MAIN: CURRENT STEP ──
step = st.session_state.step
st.header(f"Step {step+1}: {AGENDA[step]['title']}")
st.write(AGENDA[step]['prompt'])

# ── USER INPUT & ADVANCE ──
user_input = st.text_area("Your response here", key=f"resp_{step}")
if st.button("Next"):
    # Step 0: confirmation gate
    if step == 0:
        if user_input.strip().lower() == "yes":
            st.session_state.step = 1
        else:
            # reminder only
            st.warning("Are you sure you don’t want to start? Type 'Yes' when ready.")
        st.stop()

    # Steps 1+: normal flow
    # 1) record user input
    st.session_state.history.append({"role": "user", "content": user_input})

    # 2) call LLM
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=st.session_state.history,
        temperature=0.7,
    )
    answer = resp.choices[0].message.content

    # 3) record assistant reply
    st.session_state.history.append({"role": "assistant", "content": answer})

    # 4) persist history
    with open(history_file, "w") as f:
        json.dump(st.session_state.history, f, indent=2)

    # 5) advance step
    if st.session_state.step < len(AGENDA) - 1:
        st.session_state.step += 1
    st.stop()

# ── RENDER HISTORY (SESSION ONLY) ──
for msg in st.session_state.history[st.session_state.start_index:]:
    who = "👤 You:" if msg["role"] == "user" else "🤖 Mentor:"
    st.markdown(f"**{who}** {msg['content']}")
