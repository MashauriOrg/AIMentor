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

MENTOR_SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are a wise Socratic mentor guiding teams through an entrepreneurship meeting. "
        "After each team input, say “Thanks for the input.” then give constructive feedback "
        "and a clear instruction for the next step."
    )
}

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
            st.rerun()  # <-- Rerun immediately so the next view loads!
        else:
            st.error("Invalid credentials")
    st.stop()

# Only runs if the user has logged in successfully!
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

# ---- GATE STATE FOR MEETING START ----
if "gate_state" not in st.session_state:
    st.session_state.gate_state = "initial"
if "gate_question" not in st.session_state:
    st.session_state.gate_question = ""

# ---- INPUT CLEAR FLAG ----
if "clear_input" not in st.session_state:
    st.session_state.clear_input = False

# ── SIDEBAR: Agenda Navigation ──
st.sidebar.title("Agenda")
for idx, item in enumerate(AGENDA):
    marker = "➡️" if idx == st.session_state.step else ""
    st.sidebar.write(f"{marker} Step {idx+1}: {item['title']}")

# ── MAIN VIEW: Current Step ──
i = st.session_state.step
st.header(f"Step {i+1}: {AGENDA[i]['title']}")
st.write(AGENDA[i]["prompt"])

# Show gate state-specific prompt/warning
if i == 0:
    gate_state = st.session_state.gate_state
    if gate_state == "confirming":
        st.warning(
            "Are you sure you do not want to start the meeting?\n\n"
            "Please type **I want to start the meeting** or **I have a question first**."
        )
    elif gate_state == "asking_question":
        st.info("Please enter your question for the mentor.")

# ---- CLEAR INPUT BEFORE RENDERING ----
if st.session_state.clear_input:
    st.session_state[f"resp_{i}"] = ""
    st.session_state.clear_input = False

# ── RENDER CHAT HISTORY AT THE TOP ──
for msg in st.session_state.history[st.session_state.start_index:]:
    who = "👤 You:" if msg["role"] == "user" else "🤖 Mentor:"
    st.markdown(f"**{who}** {msg['content']}")

st.markdown("---")  # nice separator line before input

# ── INPUT & CHAT LOGIC (NOW AT BOTTOM) ──
user_input = st.text_area("Your response here", key=f"resp_{i}")

if st.button("Next"):

    # --- Step 0: custom meeting gate logic ---
    if i == 0:
        gate_state = st.session_state.gate_state
        response = user_input.strip()

        # --- INITIAL GATE STATE ---
        if gate_state == "initial":
            if response.lower() in ["yes", "i want to start the meeting"]:
                st.session_state.step = 1
                st.session_state.gate_state = "initial"
                st.session_state.clear_input = True
                st.rerun()
            else:
                st.session_state.gate_state = "confirming"
                st.session_state.clear_input = True
                st.rerun()

        # --- CONFIRMING STATE ---
        elif gate_state == "confirming":
            if response.lower() == "i want to start the meeting":
                st.session_state.step = 1
                st.session_state.gate_state = "initial"
                st.session_state.clear_input = True
                st.rerun()
            elif response.lower() == "i have a question first":
                st.session_state.gate_state = "asking_question"
                st.session_state.clear_input = True
                st.rerun()
            else:
                # Stay in confirming, just clear and reprompt
                st.session_state.clear_input = True
                st.rerun()

        # --- ASKING QUESTION STATE ---
        elif gate_state == "asking_question":
            # If user enters a question (not empty)
            if response:
                # Log user question
                st.session_state.history.append({"role": "user", "content": response})

                # Call LLM mentor to answer
                resp = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[MENTOR_SYSTEM_PROMPT] + st.session_state.history[1:],
                    temperature=0.7,
                )
                answer = resp.choices[0].message.content
                st.session_state.history.append({"role": "assistant", "content": answer})

                with open(history_file, "w") as f:
                    json.dump(st.session_state.history, f, indent=2)

                st.session_state.gate_state = "initial"
                st.session_state.clear_input = True
                st.rerun()
            else:
                st.warning("Please type your question first.")

        else:
            st.session_state.gate_state = "initial"
            st.session_state.clear_input = True
            st.rerun()

    # --- Steps 1+ : real chat flow ---
    else:
        # 1) log the user’s input
        st.session_state.history.append({"role": "user", "content": user_input})

        # 2) call the LLM
        messages = [MENTOR_SYSTEM_PROMPT] + st.session_state.history[1:]

        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
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
