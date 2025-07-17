import os
import json
from datetime import datetime
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="AI Mentor", layout="centered")

# ---------- LOGO + TITLE ----------
col1, col2 = st.columns([1, 7])
with col1:
    st.image("Mashauri_logo.png", width=75)
with col2:
    st.markdown(
        "<h1 style='color:#1a2533;margin-bottom:0;'>"
        "👥 AI Mentor</h1>",
        unsafe_allow_html=True,
    )

# ---------- STREAMLIT & OPENAI SETUP ----------
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_KEY)
if not OPENAI_KEY:
    st.error("Missing OPENAI_API_KEY")
    st.stop()



MENTOR_SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are a wise Socratic mentor for entrepreneurship teams. "
        "ONLY respond to the user's latest input and the current agenda question shown above. "
        "Never ask what the next agenda step is; the app controls the agenda. "
        "After each team input, thank them, give constructive feedback, and ask any follow-up questions. Ask also if they want you to to share real life experiences with them too"
        "Wait for the team to decide when to move on by typing 'Next'."
    ),
}

# ---------- AGENDA ----------
AGENDA = [
    {
        "title": "Meet Your Mentor",
        "prompt": (
            "Hello! I’m your AI Mentor with decades of entrepreneurship experience and really want to help you successfully develop your venture idea.\n\n"
            "**Capabilities:** I ask Socratic questions and draw on a curated book library.\n\n"
            "**Limitations:** I start by reviewing top-practice startup books before I answer questions, and I remember what you tell me.\n\n"
            "**Communication:** Our chats appear below. Each step will appear in the conversation.\n\n"
            "**Process:** I will guide you through the steps of the meeting and at each stage will ask you if you want to discuss more or move on to the next stage of the meeting.\n\n"
            "**Note:** On most screens, the agenda (and where we are in the agenda) will appear on the left hand side.\n\n"
            "**Are you ready to start the meeting?**\n\n"
            "Please type exactly: `Yes`"
        ),
    },
    {
        "title": "Team Objectives",
        "prompt": (
            "❗️ **Action:** What are the team’s main objectives for this venture? "
            "Please write your top 1-3 goals or hopes for this project."
        ),
    },
    {
        "title": "Welcome & Introductions",
        "prompt": (
            "❗️ **Action:** Enter each team member’s full name, one per line. Add their relevant skills if you like too.\n\n"
            "Example:\n```\nAlice Smith - Tech\nBob Johnson - Communications\nCarol Lee - Problem owner\n```"
        ),
    },
    {
        "title": "Problem Statement",
        "prompt": (
            "❗️ **Action:** Provide a one-sentence problem starting “The problem we are solving is …”.\n\n"
            "Example:\n```\nThe problem we are solving is that small businesses struggle to find affordable marketing tools.\n```"
        ),
    },
    {
        "title": "Solution Overview",
        "prompt": (
            "❗️ **Action:** Provide a one-sentence solution starting “Our solution is …”.\n\n"
            "Example:\n```\nOur solution is a mobile app that automates social-media posts for local shops.\n```"
        ),
    },
    {
        "title": "Wrap-Up",
        "prompt": (
            "Thank you for participating in this mentor meeting! "
            "If you’d like a summary or have follow-up questions, just ask.\n\n"
            "After you have your summary, presss \"Next\" again and you will get taken to the post meeting Google form.\n\n"
        ),
    },
]

# ---------- AUTHENTICATION & SESSION ----------
if "team" not in st.session_state:
    name = st.text_input("Team name")
    pw = st.text_input("Password", type="password")
    login_clicked = st.button("Login")
    if login_clicked:
        if pw == "letmein":
            st.session_state.team = name
            st.session_state.session_id = datetime.now().strftime("%Y%m%dT%H%M%S")
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

team = st.session_state.team
session_id = st.session_state.get("session_id")
if not session_id:
    st.session_state.session_id = datetime.now().strftime("%Y%m%dT%H%M%S")
    session_id = st.session_state.session_id

data_dir = "data"
os.makedirs(data_dir, exist_ok=True)
history_file = os.path.join(data_dir, f"{team}_{session_id}_history.json")

# ---------- SESSION STATE SETUP ----------
if "step" not in st.session_state:
    st.session_state.step = 0

if "state" not in st.session_state:
    st.session_state.state = "awaiting_agenda_prompt"  # or "awaiting_team_input", "awaiting_next_action", "meeting_done"

if "history" not in st.session_state:
    st.session_state.history = [MENTOR_SYSTEM_PROMPT]
    with open(history_file, "w") as f:
        json.dump(st.session_state.history, f, indent=2)

# ---------- SIDEBAR ----------
st.sidebar.title("Agenda")
for idx, item in enumerate(AGENDA):
    marker = "➡️" if idx == st.session_state.step else "  "
    st.sidebar.write(f"{marker} Step {idx+1}: {item['title']}")

i = st.session_state.step

def save_history():
    with open(history_file, "w") as f:
        json.dump(st.session_state.history, f, indent=2)

def add_mentor_message(text):
    st.session_state.history.append({"role": "assistant", "content": text})
    save_history()

def add_user_message(text):
    st.session_state.history.append({"role": "user", "content": text})
    save_history()

# ---------- MAIN CHAT AREA ----------
for msg in st.session_state.history[1:]:  # skip system prompt in display
    who = "👤 You:" if msg["role"] == "user" else "🤖 Mentor:"
    st.markdown(f"**{who}** {msg['content']}")

# Show initial agenda prompt (only once per agenda step)
if st.session_state.state == "awaiting_agenda_prompt":
    add_mentor_message(AGENDA[i]["prompt"])
    st.session_state.state = "awaiting_team_input"
    st.rerun()

# ---------- CHAT INPUT ----------
user_input = st.chat_input("Your message here...")

if user_input is not None and user_input.strip():
    response = user_input.strip()

    # Only allow "Next"/"Yes" to advance from agenda steps AFTER the first one
    is_first_agenda = st.session_state.step == 0

    if st.session_state.state == "awaiting_team_input":
        add_user_message(response)

        # If we are at the very first agenda step (Meet Your Mentor)
        if is_first_agenda:
            # Only advance if user types exactly "Yes"
            if response.lower().strip() == "yes":
                st.session_state.step += 1
                st.session_state.state = "awaiting_agenda_prompt"
                st.rerun()
            else:
                # If not "yes", prompt again
                add_mentor_message("Please type exactly: `Yes` to start the meeting.")
                st.rerun()
        else:
            # For all other agenda steps
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[MENTOR_SYSTEM_PROMPT] + st.session_state.history[1:],
                temperature=0.7,
            )
            mentor_reply = resp.choices[0].message.content
            add_mentor_message(mentor_reply)
            # Now ask if want to discuss more or move on
            add_mentor_message(
                "Would you like to discuss this topic further, or move to the next stage of the meeting?\n\n"
                "👉 Type your next comment, reply or question to continue, or type **Next** to move on to next meeting stage."
            )
            st.session_state.state = "awaiting_next_action"
            st.rerun()

    elif st.session_state.state == "awaiting_next_action":
        # Only advance step if user says "next" etc. (NEVER advance from the very first step)
        if response.lower().strip() in ["next", "yes", "continue", "go next", "y"]:
            if st.session_state.step < len(AGENDA) - 1:
                st.session_state.step += 1
                st.session_state.state = "awaiting_agenda_prompt"
                st.rerun()
            else:
                add_mentor_message("Meeting complete! Thank you for your participation. 🎉.\n\n" "Click Next again and you will be taken to the Google form to complete at the end of every mentor meeting")
                st.session_state.state = "meeting_done"
                st.rerun()
        else:
            # Continue discussing current agenda topic
            add_user_message(response)
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[MENTOR_SYSTEM_PROMPT] + st.session_state.history[1:],
                temperature=0.7,
            )
            mentor_reply = resp.choices[0].message.content
            add_mentor_message(mentor_reply)
            add_mentor_message(
                "Would you like to keep discussing, or move to the next step?\n\n"
                "Type your next comment, or **Next** to move on."
            )
            st.session_state.state = "awaiting_next_action"
            st.rerun()

    elif st.session_state.state == "meeting_done":
        st.info("This meeting is finished! You can review the chat above or close the page\n\n " "Please complete the post meeting Google form https://docs.google.com/forms/d/e/1FAIpQLSc0QN87pDYQVamKVpYtUQyfO9qPq0CWrMjc5-kqLMZ4HawILg/viewform?usp=preview")
