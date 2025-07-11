# mentor_app.py

import os
import json
import streamlit as st
from openai import OpenAI
import faiss
import numpy as np
from langchain_community.embeddings import OpenAIEmbeddings
import subprocess, os

# If the FAISS index isn't on disk, rebuild it now:
if not os.path.exists("faiss_index/index.faiss"):
    subprocess.run(["python", "ingest_books.py"], check=True)

# — AGENDA DEFINITIONS —  
INTRO_STEPS = [
    {
        "title": "Meet Your Mentor",
        "prompt": (
            "Hello! I’m your AI Mentor with decades of entrepreneurship experience.\n\n"
            "**Capabilities:**\n"
            "- I’ll guide you step-by-step through this meeting\n"
            "- I’ll ask questions and give Socratic feedback based on our book library\n\n"
            "**Limitations:**\n"
            "- I only know what’s in these books and what you tell me\n"
            "- I can’t browse the web independently (yet at least)\n\n"
            "❓  **Please type any questions you have for me** (e.g. “How do we save our chat?”)."
        )
    },
    {
        "title": "Confirm to Start",
        "prompt": (
            "When you’re ready to begin the meeting, **please type exactly**\n\n"
            "`Yes, let’s start the meeting`"
        )
    },
    {
        "title": "Agenda Overview",
        "prompt": (
            "Here is our agenda—no action yet, just review:\n\n"
            "1. Welcome & Introductions\n"
            "2. Problem Statement\n"
            "3. Solution Overview\n"
            "4. Mentor Comments\n"
            "5. Team Member Intros\n"
            "6. Mentor Summary\n"
            "7. Top Struggles\n"
            "8. Takeaways\n"
            "9. Wrap-Up\n\n"
            "When you’re ready, click **Next** to start with Step 1."
        )
    }
]

MEETING_STEPS = [
    {
        "title": "Welcome & Introductions",
        "prompt": (
            "❗️ **Action:**\n"
            "Please **type each team member’s full name**, one per line.\n\n"
            "Example:\n"
            "```\nAlice Smith\nBob Johnson\nCarol Lee\n```"
        )
    },
    {
        "title": "Problem Statement",
        "prompt": (
            "❗️ **Action:**\n"
            "Type a **one-sentence problem statement** starting with “The problem we are solving is …”.\n\n"
            "Example:\n"
            "```\nOur problem is that small businesses struggle to find affordable marketing tools.\n```"
        )
    },
    {
        "title": "Solution Overview",
        "prompt": (
            "❗️ **Action:**\n"
            "Type a **one-sentence solution overview** starting with “Our solution is …”.\n\n"
            "Example:\n"
            "```\nOur solution is a mobile app that automates social-media posts for local shops.\n```"
        )
    },
    {
        "title": "Mentor Comments",
        "prompt": (
            "📝 **Information:**\n"
            "Click **Next** to receive my feedback on your problem and solution."
        )
    },
    {
        "title": "Team Member Intros",
        "prompt": (
            "❗️ **Action:**\n"
            "Please fill in the form below for each member with these exact fields:\n"
            "- **Name** (First Last)\n"
            "- **Email**\n"
            "- **Role** on the team (e.g., CEO, Developer)\n"
            "- **Objective:** one sentence\n"
            "- **Why you joined:** one sentence\n"
            "- **Key strength:** one bullet\n\n"
            "Use the “How many members?” selector, then complete the form."
        )
    },
    {
        "title": "Mentor Summary",
        "prompt": (
            "📝 **Information:**\n"
            "Click **Next** to see my summary of your team intros and any gaps I notice."
        )
    },
    {
        "title": "Top Struggles",
        "prompt": (
            "❗️ **Action:**\n"
            "Type the **one or two biggest challenges** you’re facing right now, each on its own line.\n\n"
            "Example:\n"
            "```\nFinding customers\nManaging cash flow\n```"
        )
    },
    {
        "title": "Takeaways",
        "prompt": (
            "❗️ **Action:**\n"
            "Each member, type **one sentence** about what you got out of this meeting, one per line.\n\n"
            "Example:\n"
            "```\nAlice: I learned how to articulate our problem clearly.\nBob: I understand our next product milestone.\n```"
        )
    },
    {
        "title": "Wrap-Up",
        "prompt": (
            "📝 **Information:**\n"
            "Click **Next** to receive my final wrap-up and next-step suggestions."
        )
    }
]

AGENDA = INTRO_STEPS + MEETING_STEPS

# — CONFIG & CLIENT —
api_key = os.getenv("OPENAI_API_KEY")
client  = OpenAI(api_key=api_key)
st.set_page_config(page_title="AI Mentor", layout="centered")

# — LOAD FAISS INDEX & TEXTS (fallback) —
index     = faiss.read_index("faiss_index/index.faiss")
texts     = np.load("faiss_index/texts.npy",     allow_pickle=True)
metadatas = np.load("faiss_index/metadatas.npy", allow_pickle=True)

# — AUTHENTICATION —
if "team" not in st.session_state:
    team = st.text_input("Team name", key="team_name")
    pw   = st.text_input("Password", type="password", key="team_pw")
    if st.button("Login"):
        if pw == "letmein":
            st.session_state.team = team
        else:
            st.error("Invalid credentials")
    if "team" not in st.session_state:
        st.stop()

team = st.session_state.team
st.title(f"👥 Team {team} — Your AI Mentor")

# — PERSISTENCE: history + step index —
data_dir = "data"
os.makedirs(data_dir, exist_ok=True)
history_path = f"{data_dir}/{team}_history.json"

if "history" not in st.session_state:
    if os.path.exists(history_path):
        with open(history_path, "r") as f:
            st.session_state.history = json.load(f)
    else:
        st.session_state.history = [
            {"role": "system", "content": (
                "You are a wise mentor with decades of entrepreneurship experience. "
                "You use a Socratic style, drawing on a library of startup books."
            )}
        ]

if "step" not in st.session_state:
    st.session_state.step = 0

# — SIDEBAR: agenda navigation —
st.sidebar.title("Meeting Agenda")
for i, item in enumerate(AGENDA):
    prefix = "➡️" if i == st.session_state.step else "  "
    st.sidebar.write(f"{prefix} Step {i+1}: {item['title']}")

# — MAIN: current step —
step = st.session_state.step
st.header(f"Step {step+1}: {AGENDA[step]['title']}")
st.write(AGENDA[step]["prompt"])

# — STEP INPUT & ADVANCE —  
current_title = AGENDA[step]["title"]

if current_title == "Team Member Intros":
    with st.form("member_form"):
        num = st.number_input("How many members?", min_value=1, max_value=10, value=1)
        members = []
        for i in range(num):
            st.markdown(f"**Member {i+1} Details**")
            name      = st.text_input("Name (First Last)", key=f"name_{i}")
            email     = st.text_input("Email", key=f"email_{i}")
            role_on   = st.text_input("Role on team", key=f"role_{i}")
            objective = st.text_area("Program objective", key=f"obj_{i}", height=50)
            why       = st.text_area("Why you joined", key=f"why_{i}", height=50)
            strength  = st.text_area("Key strength", key=f"strength_{i}", height=50)
            members.append({
                "Name": name,
                "Email": email,
                "Role": role_on,
                "Objective": objective,
                "Why": why,
                "Strength": strength
            })
        submitted = st.form_submit_button("Submit members")

    if submitted:
        content = "\n\n".join(
            f"Member {i+1}:\n" + "\n".join(f"- {k}: {v}" for k, v in m.items())
            for i, m in enumerate(members)
        )
        st.session_state.history.append({"role": "user", "content": content})

        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=st.session_state.history,
            temperature=0.7
        )
        answer = resp.choices[0].message.content
        st.session_state.history.append({"role": "assistant", "content": answer})

        with open(history_path, "w") as f:
            json.dump(st.session_state.history, f, indent=2)

        # Advance to next step
        if step < len(AGENDA) - 1:
            st.session_state.step += 1

else:
    response = st.text_area("Your response here", key=f"step_{step}")
    if st.button("Next"):
        st.session_state.history.append({
            "role": "user",
            "content": f"{current_title} response: {response}"
        })
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=st.session_state.history,
            temperature=0.7
        )
        answer = resp.choices[0].message.content
        st.session_state.history.append({"role": "assistant", "content": answer})

        with open(history_path, "w") as f:
            json.dump(st.session_state.history, f, indent=2)

        # Advance to next step
        if step < len(AGENDA) - 1:
            st.session_state.step += 1

# — RENDER HISTORY (newest first) —
for msg in reversed(st.session_state.history[1:]):
    prefix = "👤 You:" if msg["role"] == "user" else "🤖 Mentor:"
    st.markdown(f"**{prefix}** {msg['content']}")

