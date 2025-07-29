import os
import json
from datetime import datetime
import streamlit as st
from openai import OpenAI
from book_retrieval import search_books

# ---------- CONFIGURATION ----------
MEETING_SCRIPTS_DIR = "meeting_scripts"

# ---------- UTILITIES ----------
def load_agenda(meeting_name: str) -> list[dict] | None:
    filename = f"{meeting_name}.json"
    path = os.path.join(MEETING_SCRIPTS_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ---------- PAGE SETUP ----------
st.set_page_config(page_title="Mashauri AI Mentor", layout="centered")

# ---------- HEADER ----------
col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    st.image("Mashauri_logo.png", width=75)
with col2:
    st.markdown(
        "<h1 style='margin-bottom:0;'>👥 SAVI<br/>(your USSAVI AI Mentor)</h1>",
        unsafe_allow_html=True,
    )
with col3:
    st.image("SAVI HQ.png", width=100)

# ---------- OPENAI CLIENT ----------
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_KEY:
    st.error("Missing OPENAI_API_KEY")
    st.stop()
client = OpenAI(api_key=OPENAI_KEY)

# ---------- SYSTEM PROMPT ----------
MENTOR_SYSTEM_PROMPT = {
    "role": "system",
    "content": (
    "You are SAVI, a seasoned entrepreneurship mentor in her 50s with a warm but no-nonsense personality. "
    "Your mission is to help entrepreneurship teams build ventures that truly solve customer problems and generate real revenue. "
    "You genuinely care about their success – you celebrate their wins, reassure them when they struggle, and aren’t afraid to deliver tough love when needed. "
    "\n\n"
    "When you respond:\n"
    "- Challenge their thinking gently but firmly if their assumptions seem weak or untested.\n"
    "- Sometimes use a thoughtful pause (e.g. 'Hmm…') to make them reflect.\n"
    "- Share short, relevant case studies or real examples (from the indexed book library or reputable sources) when appropriate, to illustrate lessons or spark ideas.\n"
    "- Occasionally use light humor or encouragement to keep the mood positive and human.\n"
    "\n\n"
    "Rules for your interactions:\n"
    "- ONLY respond to the team's latest input and the current agenda question shown above.\n"
    "- Never ask what the next agenda step is – the app controls the agenda.\n"
    "- After every response, thank them for sharing, give constructive feedback, and ask a follow-up question to deepen their thinking.\n"
    "- Occasionally ask, 'Would you like me to share a real-life story about this?' to invite them to learn from experience.\n"
    "- If you see signs they’re stuck or playing it too safe, nudge them with questions like 'What would make this bolder?' or 'Are you sure your customers would actually pay for that?'\n"
    "- Always balance kindness and honesty – think of yourself as the mentor who will hug them when they need it, but also tell them when their idea needs work.\n"
    "\n\n"
    "End each exchange by inviting the team to keep exploring or type 'Next' to move forward."
  
    ),
}

# ---------- AUTHENTICATION & SESSION ----------
if "team" not in st.session_state:
    # Login form
    name = st.text_input("Team name")
    pw = st.text_input("Password", type="password")
    st.write("Please select your meeting type from the dropdown list")
    # List available meeting scripts directly
    scripts = [f[:-5] for f in os.listdir(MEETING_SCRIPTS_DIR) if f.endswith(".json")]
    meeting_type = st.selectbox("Meeting type", scripts)
    if st.button("Login"):
        if pw == "guideme":
            st.session_state.team = name
            st.session_state.session_id = datetime.now().strftime("%Y%m%dT%H%M%S")
            st.session_state.meeting_type = meeting_type
            # Load the selected agenda from JSON files
            st.session_state.agenda = load_agenda(meeting_type)
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

team = st.session_state.team
session_id = st.session_state.session_id
agenda = st.session_state.get("agenda")

# ---------- HISTORY & STATE ----------
data_dir = os.getenv(
    "CHAT_HISTORY_DIR",
    os.path.join(os.getcwd(), "data", "faiss_index", "chat_history"),
)
os.makedirs(data_dir, exist_ok=True)
history_file = os.path.join(data_dir, f"{team}_{session_id}_history.json")

if "step" not in st.session_state:
    st.session_state.step = 0
if "state" not in st.session_state:
    st.session_state.state = "awaiting_agenda_prompt" if agenda else "awaiting_team_input"
if "history" not in st.session_state:
    st.session_state.history = [MENTOR_SYSTEM_PROMPT]
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(st.session_state.history, f, indent=2)

# ---------- SIDEBAR ----------
st.sidebar.title("Agenda")
if agenda:
    for idx, item in enumerate(agenda):
        marker = "➡️" if idx == st.session_state.step else "  "
        st.sidebar.write(f"{marker} Step {idx+1}: {item['title']}")
else:
    st.sidebar.write("No agenda selected.")

# ---------- HELPERS ----------
def save_history():
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(st.session_state.history, f, indent=2)

def add_mentor_message(text: str):
    st.session_state.history.append({"role": "assistant", "content": text})
    save_history()

def add_user_message(text: str):
    st.session_state.history.append({"role": "user", "content": text})
    save_history()

# ---------- RENDER MESSAGES ----------
for msg in st.session_state.history[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------- AGENDA PROMPT ----------
if st.session_state.state == "awaiting_agenda_prompt" and agenda:
    add_mentor_message(agenda[st.session_state.step]["prompt"])
    st.session_state.state = "awaiting_team_input"
    st.rerun()

# ---------- USER INPUT ----------
user_input = st.chat_input("Your message here...")
if user_input:
    response = user_input.strip()
    add_user_message(response)

    is_first = st.session_state.step == 0
    mt = st.session_state.get("meeting_type", "")

    if st.session_state.state == "awaiting_team_input":
        if is_first and agenda and mt != "General Conversation" and response.lower() != "yes":
            add_mentor_message("Please type exactly: `Yes` to start the meeting.")
            st.rerun()

        snippets = []
        context_msgs = []
        if response and not (is_first and agenda and mt != "General Conversation"):
            snippets = search_books(response)
            if snippets:
                excerpts = "\n---\n".join(snippets)
                context_msgs.append({"role": "system", "content": "Relevant book excerpts:\n" + excerpts})
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[MENTOR_SYSTEM_PROMPT] + context_msgs + st.session_state.history[1:],
                temperature=0.7,
            )
            mentor_reply = resp.choices[0].message.content
            add_mentor_message(mentor_reply)

        if agenda:
            add_mentor_message(
                "Would you like to move to the next stage of the agenda or continue to discuss this topic further?\n\n"
                "👉 Type your next comment, reply or question to continue, or type **Next** to move on."
            )
            st.session_state.state = "awaiting_next_action"
        else:
            st.session_state.state = "awaiting_team_input"
        st.rerun()

    if st.session_state.state == "awaiting_next_action":
        if response.lower() in ["next", "yes", "continue", "go next", "y"] and agenda:
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
            snippets = search_books(response)
            context_msgs = []
            if snippets:
                excerpts = "\n---\n".join(snippets)
                context_msgs.append({"role": "system", "content": "Relevant book excerpts:\n" + excerpts})
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[MENTOR_SYSTEM_PROMPT] + context_msgs + st.session_state.history[1:],
                temperature=0.7,
            )
            mentor_reply = resp.choices[0].message.content
            add_mentor_message(mentor_reply)
            add_mentor_message(
                "Would you like to keep discussing, or move to the next step?\n\n"
                "Type your next comment, or **Next** to move on."
            )
            st.rerun()

    if st.session_state.state == "meeting_done":
        st.info(
            "This meeting is finished! You can review the chat above or close the page\n\n "
            "Please complete the post meeting Google form https://docs.google.com/forms/d/e/1FAIpQLSc0QN87pDYQVamKVpYtUQyfO9qPq0CWrMjc5-kqLMZ4HawILg/viewform?usp=preview"
        )
