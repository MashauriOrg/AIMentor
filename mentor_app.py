import os
import json
import streamlit as st
from openai import OpenAI

# STREAMLIT & OPENAI SETUP
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
client     = OpenAI(api_key=OPENAI_KEY)
if not OPENAI_KEY:
    st.error("Missing OPENAI_API_KEY")
    st.stop()

st.set_page_config(page_title="AI Mentor", layout="centered")

MENTOR_SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are a wise Socratic mentor guiding teams through an entrepreneurship meeting. "
        "Never say anything about moving to the next agenda step or advancing. "
        "After each team input, say 'Thanks for the input,' then give constructive feedback, ask thoughtful follow-up questions if appropriate, and guide the discussion. "
        "Wait for the team to decide when they are ready to move to the next step."
    )
}

# AGENDA
AGENDA = [
    {
        "title": "Meet Your Mentor",
        "prompt": (
            "Hello! I’m your AI Mentor with decades of entrepreneurship experience—ready to help you develop your venture.\n\n"
            "**Capabilities:** I ask Socratic questions and draw on a curated book library.\n\n"
            "**Limitations:** I start by reviewing top-practice startup books before I answer questions, and I remember what you tell me.\n\n"
            "**Communication:** Our chats appear below. Each step will appear in the conversation.\n\n"
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

# AUTHENTICATION
if "team" not in st.session_state:
    name          = st.text_input("Team name")
    pw            = st.text_input("Password", type="password")
    login_clicked = st.button("Login")
    if login_clicked:
        if pw == "letmein":
            st.session_state.team = name
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

team = st.session_state.team
st.title(f"👥 Team {team} — AI Mentor")

# PERSISTENCE
data_dir     = "data"
os.makedirs(data_dir, exist_ok=True)
history_file = os.path.join(data_dir, f"{team}_history.json")

if "history" not in st.session_state:
    if os.path.exists(history_file) and os.path.getsize(history_file) > 0:
        st.session_state.history = json.load(open(history_file, "r"))
    else:
        st.session_state.history = [
            MENTOR_SYSTEM_PROMPT
        ]



if "start_index" not in st.session_state:
    st.session_state.start_index = len(st.session_state.history)

if "step" not in st.session_state:
    st.session_state.step = 0

if "conversation_state" not in st.session_state:
    st.session_state.conversation_state = "awaiting_team_input"  # or 'awaiting_mentor_reply', 'meeting_done'

if "clear_input" not in st.session_state:
    st.session_state.clear_input = False

i = st.session_state.step

# SIDEBAR: Agenda Navigation
st.sidebar.title("Agenda")
for idx, item in enumerate(AGENDA):
    marker = "➡️" if idx == i else ""
    st.sidebar.write(f"{marker} Step {idx+1}: {item['title']}")

# CLEAR INPUT BEFORE RENDERING
if st.session_state.clear_input:
    st.session_state[f"resp_{i}"] = ""
    st.session_state.clear_input = False

# CHAT HISTORY
for msg in st.session_state.history[st.session_state.start_index:]:
    if msg["role"] == "system":
        continue
    who = "👤 You:" if msg["role"] == "user" else "🤖 Mentor:"
    st.markdown(f"**{who}** {msg['content']}")

st.markdown("---")

def save_history():
    with open(history_file, "w") as f:
        json.dump(st.session_state.history, f, indent=2)

def add_mentor_message(text):
    st.session_state.history.append({"role": "assistant", "content": text})
    save_history()

def add_user_message(text):
    st.session_state.history.append({"role": "user", "content": text})
    save_history()

# MAIN STATE MACHINE

if st.session_state.conversation_state == "awaiting_team_input" and (
    len(st.session_state.history) == st.session_state.start_index or
    st.session_state.history[-1]["content"] != AGENDA[i]["prompt"]
):
    add_mentor_message(AGENDA[i]["prompt"])
    st.session_state.clear_input = True
    st.rerun()

user_input = st.text_area("Your response here", key=f"resp_{i}")

if st.button("Next"):

    # TEAM INPUTS TO AGENDA PROMPT OR TO CONTINUE CHAT
    if st.session_state.conversation_state == "awaiting_team_input":
        response = user_input.strip()
        if response:
            # If user types "next", advance to the next agenda item
            if response.lower() in ["next", "yes", "y", "ready", "continue"]:
                if st.session_state.step < len(AGENDA) - 1:
                    st.session_state.step += 1
                    st.session_state.conversation_state = "awaiting_team_input"
                    st.session_state.clear_input = True
                    st.rerun()
                else:
                    # Meeting done!
                    add_mentor_message("Thank you for your contributions! Meeting complete. 🎉")
                    st.session_state.conversation_state = "meeting_done"
                    st.session_state.clear_input = True
                    st.rerun()
            else:
                add_user_message(response)
                # Mentor responds to input
                resp = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[MENTOR_SYSTEM_PROMPT] + st.session_state.history[1:],
                    temperature=0.7,
                )
                mentor_reply = resp.choices[0].message.content
                add_mentor_message(mentor_reply)
                # (App, not mentor, posts navigation hint below)
                st.session_state.clear_input = True
                st.rerun()
        else:
            st.warning("Please enter a response before clicking Next.")

    elif st.session_state.conversation_state == "meeting_done":
        st.info("This meeting is finished! You can review the chat above or restart.")

    else:
        st.session_state.conversation_state = "awaiting_team_input"
        st.session_state.clear_input = True
        st.rerun()

# -- APP-LEVEL NAVIGATION PROMPT (shows after any mentor reply, except at end) --
if (
    st.session_state.conversation_state == "awaiting_team_input"
    and len(st.session_state.history) > st.session_state.start_index + 1
    and st.session_state.history[-1]["role"] == "assistant"
    and st.session_state.step < len(AGENDA)
):
    st.markdown(
        "<div style='background:#f8f9fa; border-left:4px solid #007bff; padding:0.75em 1em; margin:1em 0 1.5em 0;'>"
        "<b>Would you like to keep discussing this topic, or move to the next step?</b><br>"
        "Type your next comment or question, or type <b>Next</b> to move on.</div>",
        unsafe_allow_html=True,
    )
