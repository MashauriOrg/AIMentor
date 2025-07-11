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
AGENDA = [
    {
        "title": "Meet Your Mentor",
        "prompt": (
            "Hello! I’m your AI Mentor with decades of entrepreneurship experience—ready to help you develop your venture.\n\n"
            "**Capabilities:** I ask Socratic questions and draw on a curated book library.\n\n"
            "**Limitations:** I start from top startup books and remember your inputs, but I’m still learning—be patient!\n\n"
            "**Communication:** Your chats appear below; instructions appear above the input box.\n\n"
            "**Are you ready to start the meeting?**\n\n"
            "Please type exactly `Yes` to begin, or anything else to delay."
        )
    },
    {
        "title": "Welcome & Introductions",
        "prompt": (
            "❗️ **Action:** Enter each team member’s full name, one per line."
        )
    },
    {
        "title": "Problem Statement",
        "prompt": (
            "❗️ **Action:** Provide a one-sentence problem starting “Our problem is …”."
        )
    },
    {
        "title": "Solution Overview",
        "prompt": (
            "❗️ **Action:** Provide a one-sentence solution starting “Our solution is …”."
        )
    },
    {
        "title": "Wrap-Up",
        "prompt": (
            "Click **Next** to receive your mentor’s final wrap-up."
        )
    }
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
