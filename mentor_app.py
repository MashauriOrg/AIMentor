import os
import json
from datetime import datetime
import streamlit as st
from openai import OpenAI
from book_retrieval import search_books

def load_agenda(meeting_name: str) -> list[dict] | None:
    """Load an agenda JSON file from the meeting_scripts directory."""
    path = os.path.join("meeting_scripts", f"{meeting_name}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)

st.set_page_config(page_title="Mashauri AI Mentor", layout="centered")

# ---------- LOGO + TITLE ----------

col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    st.image("Mashauri_logo.png", width=75)
with col2:
    st.markdown(
        "<h1 style='color:inherit;margin-bottom:0;'>👥 SAVI<br/>(your USSAVI AI Mentor)</h1>",
        unsafe_allow_html=True,
    )
with col3:
    st.image("SAVI HQ.png", width=100)

# ---------- STREAMLIT & OPENAI SETUP ----------
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_KEY)
if not OPENAI_KEY:
    st.error("Missing OPENAI_API_KEY")
    st.stop()

# ---------- SYSTEM PROMPT ----------
MENTOR_SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are a seasoned Socratic entrepreneurship mentor for entrepreneurship teams. "
        "When appropriate, provide short case studies or real examples drawn from the indexed book library or reputable web sources. "
        "After each response, ask whether the team would like you to share a relevant experience. "
        "ONLY respond to the user's latest input and the current agenda question shown above. "
        "Never ask what the next agenda step is; the app controls the agenda. "
        "After each team input, thank them, give constructive feedback, and ask any follow-up questions. "
        "Ask also if they want you to share real life experiences with them too. "
        "Wait for the team to decide when to move on by typing 'Next'."
    ),
}
# Agendas are loaded dynamically from meeting_scripts/*.json
# ---------- AGENDA ----------
#AGENDA = load_agenda("kickoff")
#if AGENDA is None:
#    st.error("Couldn't find meeting_scripts/kickoff.json")
#   st.stop()

# ---------- AUTHENTICATION & SESSION ----------
if "team" not in st.session_state:
    name = st.text_input("Team name")
    pw = st.text_input("Password", type="password")
    meetings = ["General Conversation"] + [
        f[:-5] for f in os.listdir("meeting_scripts") if f.endswith(".json")
    ]
    meeting_type = st.selectbox("Meeting type", meetings)
    login_clicked = st.button("Login")
    if login_clicked:
        if pw == "guideme":
            st.session_state.team = name
            st.session_state.session_id = datetime.now().strftime("%Y%m%dT%H%M%S")
            st.session_state.meeting_type = meeting_type
            if meeting_type == "General Conversation":
                st.session_state.agenda = None
            else:
                st.session_state.agenda = load_agenda(meeting_type)
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

team = st.session_state.team
session_id = st.session_state.get("session_id")
if not session_id:
    st.session_state.session_id = datetime.now().strftime("%Y%m%dT%H%M%S")
    session_id = st.session_state.session_id

if "agenda" not in st.session_state:
    mt = st.session_state.get("meeting_type")
    if mt == "General Conversation":
        st.session_state.agenda = None
    elif mt:
        st.session_state.agenda = load_agenda(mt)
   

#data_dir = "data" Delee these 3 lines when working
# use an env var if set, otherwise default to ./data
#data_dir = os.getenv("CHAT_HISTORY_DIR", "data")


# use CHAT_HISTORY_DIR if set, otherwise write under Render’s persistent disk
#data_dir = os.getenv("CHAT_HISTORY_DIR", "/mnt/data/faiss_index/chat_history")
#os.makedirs(data_dir, exist_ok=True)

# use CHAT_HISTORY_DIR if set, otherwise write under a local ./data folder
data_dir = os.getenv(
    "CHAT_HISTORY_DIR",
    os.path.join(os.getcwd(), "data", "faiss_index", "chat_history"),
)
os.makedirs(data_dir, exist_ok=True)



history_file = os.path.join(data_dir, f"{team}_{session_id}_history.json")

# ---------- SESSION STATE SETUP ----------
if "step" not in st.session_state:
    st.session_state.step = 0

if "state" not in st.session_state:
    if st.session_state.get("agenda"):
        st.session_state.state = "awaiting_agenda_prompt"
    else:
        st.session_state.state = "awaiting_team_input"

if "history" not in st.session_state:
    st.session_state.history = [MENTOR_SYSTEM_PROMPT]
    with open(history_file, "w") as f:
        json.dump(st.session_state.history, f, indent=2)

# ---------- SIDEBAR ----------
st.sidebar.title("Agenda")
agenda = st.session_state.get("agenda")
if agenda:
    for idx, item in enumerate(agenda):
        marker = "➡️" if idx == st.session_state.step else "  "
        st.sidebar.write(f"{marker} Step {idx+1}: {item['title']}")
else:
    st.sidebar.write("No agenda selected.")

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
for msg in st.session_state.history[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])



# Show initial agenda prompt (only once per agenda step)
if st.session_state.state == "awaiting_agenda_prompt" and agenda:
    add_mentor_message(agenda[i]["prompt"])
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
              
                add_mentor_message("Please type exactly: `Yes` to start the meeting.")
                st.rerun()
        else:
          
            snippets = search_books(response)
            context_msgs = []
            if snippets:
                text = "\n---\n".join(snippets)
                context_msgs.append({
                    "role": "system",
                    "content": "Relevant book excerpts:\n" + text,
                })

            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[MENTOR_SYSTEM_PROMPT] + context_msgs + st.session_state.history[1:],
                temperature=0.7,
            )
            mentor_reply = resp.choices[0].message.content
            add_mentor_message(mentor_reply)
            if agenda:
                add_mentor_message(
                    "Would you like to discuss this topic further, or move to the next stage of the meeting?\n\n"
                    "👉 Type your next comment, reply or question to continue, or type **Next** to move on to next meeting stage."
                )
                st.session_state.state = "awaiting_next_action"
            else:
                st.session_state.state = "awaiting_team_input"
            st.rerun()

    elif st.session_state.state == "awaiting_next_action":
        # Only advance step if user says "next" etc. (NEVER advance from the very first step)
        if response.lower().strip() in ["next", "yes", "continue", "go next", "y"] and agenda:
            add_user_message(response)  # record the user's request to advance
            if st.session_state.step < len(agenda) - 1:
                st.session_state.step += 1
                st.session_state.state = "awaiting_agenda_prompt"
                st.rerun()
            else:
                add_mentor_message(
                    "Meeting complete! Thank you for your participation. 🎉.\n\n"
                    "Click Next again and you will be taken to the Google form to complete at the end of every mentor meeting"
                )
                st.session_state.state = "meeting_done"
                st.rerun()
        else:
            # Continue discussing current agenda topic
            add_user_message(response)
            snippets = search_books(response)
            context_msgs = []
            if snippets:
                text = "\n---\n".join(snippets)
                context_msgs.append({
                    "role": "system",
                    "content": "Relevant book excerpts:\n" + text,
                })
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[MENTOR_SYSTEM_PROMPT] + context_msgs + st.session_state.history[1:],
                temperature=0.7,
            )
            mentor_reply = resp.choices[0].message.content
            add_mentor_message(mentor_reply)
            if agenda:
                add_mentor_message(
                    "Would you like to keep discussing, or move to the next step?\n\n"
                    "Type your next comment, or **Next** to move on."
                )
                st.session_state.state = "awaiting_next_action"
            st.rerun()

    elif st.session_state.state == "meeting_done":
        st.info("This meeting is finished! You can review the chat above or close the page\n\n " "Please complete the post meeting Google form https://docs.google.com/forms/d/e/1FAIpQLSc0QN87pDYQVamKVpYtUQyfO9qPq0CWrMjc5-kqLMZ4HawILg/viewform?usp=preview")
