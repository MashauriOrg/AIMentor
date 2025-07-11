# mentor_app.py

import os, json, streamlit as st, openai

# 0) Setup
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    st.error("Missing OPENAI_API_KEY")
    st.stop()
st.set_page_config(page_title="AI Mentor", layout="centered")

# 1) Simple agenda
AGENDA = [
    {"title":"Meet Your Mentor",
     "prompt":"Hello! I’m your AI Mentor. Ask me anything or type any questions now."},
    {"title":"Confirm to Start",
     "prompt":"When you’re ready, type exactly:\n\n`Yes, let’s start the meeting`"},
    {"title":"Welcome & Introductions",
     "prompt":"❗️ **Action:** Enter each team member’s full name, one per line."},
    {"title":"Problem Statement",
     "prompt":"❗️ **Action:** One-sentence problem starting “Our problem is …”"},
    {"title":"Solution Overview",
     "prompt":"❗️ **Action:** One-sentence solution starting “Our solution is …”"},
    {"title":"Wrap-Up",
     "prompt":"Click **Next** to receive your mentor’s final wrap-up."}
]

# 2) Authentication
if "team" not in st.session_state:
    name = st.text_input("Team name")
    pw   = st.text_input("Password", type="password")
    if st.button("Login") and pw == "letmein":
        st.session_state.team = name
    else:
        if st.button("Login"): st.error("Invalid credentials")
    st.stop()

team = st.session_state.team
st.title(f"👥 Team {team} — AI Mentor")

# 3) History & step persistence
data_dir = "data"; os.makedirs(data_dir, exist_ok=True)
hist_file = os.path.join(data_dir, f"{team}_history.json")

if "history" not in st.session_state:
    if os.path.exists(hist_file):
        st.session_state.history = json.load(open(hist_file))
    else:
        st.session_state.history = [{
            "role":"system",
            "content":(
                "You are a wise AI mentor. You ask Socratic questions "
                "and draw on a curated library of entrepreneurship books."
            )
        }]

if "step" not in st.session_state:
    st.session_state.step = 0

# 4) Sidebar agenda
st.sidebar.title("Agenda")
for idx, item in enumerate(AGENDA):
    mark = "➡️" if idx == st.session_state.step else ""
    st.sidebar.write(f"{mark} {idx+1}. {item['title']}")

# 5) Display current step
i = st.session_state.step
st.header(f"Step {i+1}: {AGENDA[i]['title']}")
st.write(AGENDA[i]["prompt"])

# 6) Capture input & call OpenAI
user_input = st.text_area("Your response here", key=f"resp_{i}")
if st.button("Next"):
    st.session_state.history.append({"role":"user","content":user_input})
    resp = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=st.session_state.history,
        temperature=0.7
    )
    answer = resp.choices[0].message.content
    st.session_state.history.append({"role":"assistant","content":answer})

    # persist & advance
    with open(hist_file,"w") as f:
        json.dump(st.session_state.history, f, indent=2)
    if st.session_state.step < len(AGENDA)-1:
        st.session_state.step += 1
    st.experimental_rerun()

# 7) Show chat (newest first)
for msg in reversed(st.session_state.history[1:]):
    who = "👤 You:" if msg["role"]=="user" else "🤖 Mentor:"
    st.markdown(f"**{who}** {msg['content']}")
