import os
import json
import streamlit as st
from openai import OpenAI

# ---- LOGO & HEADER ----
col1, col2 = st.columns([1, 6])
with col1:
    st.image("Mashauri_logo.png", width=75)
with col2:
    st.markdown("<h1 style='color:#B00; margin-bottom:0;'>MashaurMentorBot</h1>", unsafe_allow_html=True)

# ---- OPENAI SETUP ----
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

# ---- FULL AGENDA ----
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
        "title": "Team Objectives",
        "prompt": (
            "❗️ **Action:** What are the team’s main objectives for this venture? "
            "Please write your top 1-3 goals or hopes for this project."
        )
    },
    {
        "title": "Team Member Names",
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
        "title": "Team Member Skills",
        "prompt": (
            "❗️ **Action:** For each team member: Please share why you’re part of this venture and what (if any) special skills, expertise, or experience you bring to the team."
        )
    },
    {
        "title": "Immediate Issues",
        "prompt": (
            "Are there any immediate issues or challenges you’d like to discuss with your mentor? "
            "Feel free to ask about anything on your mind."
        )
    },
    {
        "title": "Wrap-Up",
        "prompt": "Here’s a summary of your meeting and some next steps!"
    },
    {
        "title": "Submit Meeting Template",
        "prompt": (
            "Please complete the Mashauri meeting template for submission. "
            "Include your team name, members, objectives, problem statement, solution, key skills, and next steps."
        )
    },
]

# ---- AUTHENTICATION ----
if "team" not in st.session_state:
    col1, col2 = st.columns([1, 6])
    with col1:
        st.image("Mashauri_logo.png", width=75)
    with col2:
        st.markdown("<h1 style='color:#B00; margin-bottom:0;'>MashaurMentorBot</h1>", unsafe_allow_html=True)
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

# ---- PERSISTENCE ----
data_dir     = "data"
os.makedirs(data_dir, exist_ok=True)
history_file = os.path.join(data_dir, f"{team}_history.json")

if "history" not in st.session_state:
    if os.path.exists(history_file) and os.path.getsize(history_file) > 0:
        st.session_state.history = json.load(open(history_file, "r"))
    else:
        st.session_state.history = [MENTOR_SYSTEM_PROMPT]

if "start_index" not in st.session_state:
    st.session_state.start_index = len(st.session_state.history)
if "step" not in st.session_state:
    st.session_state.step = 0

# ---- State Tracking for Special Steps ----
if "member_index" not in st.session_state:
    st.session_state.member_index = 0
if "member_list" not in st.session_state:
    st.session_state.member_list = []
if "immediate_issues_count" not in st.session_state:
    st.session_state.immediate_issues_count = 0

if "conversation_state" not in st.session_state:
    st.session_state.conversation_state = "awaiting_team_input"
if "clear_input" not in st.session_state:
    st.session_state.clear_input = False

i = st.session_state.step

# ---- SIDEBAR: Agenda Navigation ----
st.sidebar.title("Agenda")
for idx, item in enumerate(AGENDA):
    marker = "➡️" if idx == i else ""
    st.sidebar.write(f"{marker} Step {idx+1}: {item['title']}")

# ---- CLEAR INPUT BEFORE RENDERING ----
if st.session_state.clear_input:
    st.session_state[f"resp_{i}"] = ""
    st.session_state.clear_input = False

# ---- CHAT HISTORY ----
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

# ---- MAIN FLOW LOGIC ----

# At the start of each step, prompt team as mentor message
if st.session_state.conversation_state == "awaiting_team_input" and (
    len(st.session_state.history) == st.session_state.start_index or
    st.session_state.history[-1]["content"] != AGENDA[i]["prompt"]
):
    # Special case: Step 5, handle individual team members one by one
    if i == 5 and st.session_state.member_index < len(st.session_state.member_list):
        current_member = st.session_state.member_list[st.session_state.member_index]
        add_mentor_message(f"Team member: **{current_member}**, please share why you're part of this venture and any special skills, expertise, or experience you bring to the team.")
    else:
        add_mentor_message(AGENDA[i]["prompt"])
    st.session_state.clear_input = True
    st.rerun()

user_input = st.text_area("Your response here", key=f"resp_{i}")

if st.button("Next"):

    if st.session_state.conversation_state == "awaiting_team_input":
        response = user_input.strip()
        if response:
            # ---- Step 2: Capture Team Members List ----
            if i == 2:
                members = [line.strip() for line in response.split('\n') if line.strip()]
                st.session_state.member_list = members
                add_user_message(response)
                mentor_reply = "Thanks for sharing your team members!"
                add_mentor_message(mentor_reply)
                st.session_state.step += 1
                st.session_state.clear_input = True
                st.rerun()

            # ---- Step 5: Team Member Skills, loop through each member ----
            elif i == 5 and st.session_state.member_index < len(st.session_state.member_list):
                current_member = st.session_state.member_list[st.session_state.member_index]
                add_user_message(f"{current_member}: {response}")
                resp = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[MENTOR_SYSTEM_PROMPT] + st.session_state.history[1:],
                    temperature=0.7,
                )
                mentor_reply = resp.choices[0].message.content
                add_mentor_message(mentor_reply)
                st.session_state.member_index += 1
                st.session_state.clear_input = True
                # If not last member, stay on same step; else advance step
                if st.session_state.member_index < len(st.session_state.member_list):
                    st.rerun()
                else:
                    # Summarize team skills
                    add_mentor_message("Great! That's all team members. Here’s a quick summary of your team's skills and any gaps the mentor sees.")
                    st.session_state.step += 1
                    st.session_state.member_index = 0  # Reset for future meetings
                    st.session_state.clear_input = True
                    st.rerun()

            # ---- Step 6: Immediate Issues with up to 4 cycles ----
            elif i == 6:
                add_user_message(response)
                resp = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[MENTOR_SYSTEM_PROMPT] + st.session_state.history[1:],
                    temperature=0.7,
                )
                mentor_reply = resp.choices[0].message.content
                add_mentor_message(mentor_reply)
                st.session_state.immediate_issues_count += 1
                st.session_state.clear_input = True
                if st.session_state.immediate_issues_count < 4:
                    add_mentor_message(
                        f"Would you like to discuss another issue? (You have {4 - st.session_state.immediate_issues_count} more issue(s) before wrap-up, or type 'Next' to move on.)"
                    )
                    st.rerun()
                else:
                    add_mentor_message(
                        "You've reached the maximum number of immediate issues for this meeting. Let's move to the wrap-up."
                    )
                    st.session_state.step += 1
                    st.session_state.immediate_issues_count = 0
                    st.session_state.clear_input = True
                    st.rerun()

            # ---- Normal "Next" logic for all other steps ----
            elif response.lower() in ["next", "yes", "y", "ready", "continue"]:
                if st.session_state.step < len(AGENDA) - 1:
                    st.session_state.step += 1
                    st.session_state.conversation_state = "awaiting_team_input"
                    st.session_state.clear_input = True
                    st.rerun()
                else:
                    add_mentor_message("Thank you for your contributions! Meeting complete. 🎉")
                    st.session_state.conversation_state = "meeting_done"
                    st.session_state.clear_input = True
                    st.rerun()
            else:
                # Standard chat/mentor response
                add_user_message(response)
                resp = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[MENTOR_SYSTEM_PROMPT] + st.session_state.history[1:],
                    temperature=0.7,
                )
                mentor_reply = resp.choices[0].message.content
                add_mentor_message(mentor_reply)
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

# ---- APP-LEVEL NAVIGATION PROMPT ----
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
