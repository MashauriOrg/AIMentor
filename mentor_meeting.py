import streamlit as st
import os

# ---- TEAM/PASSWORD ----
teams = ["Team 1", "Team 2", "Team 3", "Team 4", "Team 5"]
team_passwords = {
    "Team 1": "apple123",
    "Team 2": "banana234",
    "Team 3": "cherry345",
    "Team 4": "date456",
    "Team 5": "elder567"
}
team = st.selectbox("Select your team:", teams)
password = st.text_input("Enter your team password:", type="password")

# Script location
script_file = "meeting_scripts/meeting_1_kickoff.txt"

if password != team_passwords[team]:
    if password:
        st.error("Incorrect password. Please try again.")
    st.stop()
else:
    st.success("Access granted.")

# ---- Script Loading ----
if not os.path.exists(script_file):
    st.error(f"Script file '{script_file}' not found!")
    st.stop()
with open(script_file, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f.read().split('---') if line.strip()]

# ---- Session State ----
if "meeting_step" not in st.session_state or st.session_state.get("team") != team:
    st.session_state.meeting_step = 0
    st.session_state.team = team
if "inputs" not in st.session_state or st.session_state.get("team") != team:
    st.session_state.inputs = {}
if "mentor_chat" not in st.session_state or st.session_state.get("team") != team:
    st.session_state.mentor_chat = []

# ---- Meeting Navigation ----
st.header(f"Mentor Meeting: {team}")

step = st.session_state.meeting_step
script_block = lines[step].strip() if step < len(lines) else None

# --- Show main script step ---
if script_block:
    if script_block.startswith("INPUT:"):
        label = script_block[6:].strip()
        value = st.text_input(label, value=st.session_state.inputs.get(label, ""), key=f"input_{step}")
        if st.button("Next"):
            st.session_state.inputs[label] = value
            st.session_state.meeting_step += 1
        if st.button("Back") and step > 0:
            st.session_state.meeting_step -= 1
    elif script_block.startswith("FORM:"):
        st.subheader("Feedback Form")
        feedback = st.text_area("Feedback:", value=st.session_state.inputs.get("Feedback", ""), key=f"form_{step}")
        if st.button("Submit"):
            st.session_state.inputs["Feedback"] = feedback
            st.success("Thank you for your feedback!")
            st.session_state.meeting_step += 1
        if st.button("Back") and step > 0:
            st.session_state.meeting_step -= 1
    else:
        st.write(script_block)
        if st.button("Next"):
            st.session_state.meeting_step += 1
        if st.button("Back") and step > 0:
            st.session_state.meeting_step -= 1
else:
    st.success("Meeting complete!")
    st.write("Your saved answers:")
    st.write(st.session_state.inputs)
    if st.button("Restart"):
        st.session_state.meeting_step = 0
        st.session_state.inputs = {}

# ---- Mentor Q&A Interactivity ----
st.markdown("---")
st.subheader("Ask the Mentor (general questions)")
q = st.text_input("Type a question for your mentor:", key="mentorq")
if st.button("Ask Mentor"):
    # Simulated mentor reply (replace with book Q&A)
    answer = f"Mentor says: Sorry, Q&A with books not implemented yet (demo response for: {q})"
    st.session_state.mentor_chat.append(("You", q))
    st.session_state.mentor_chat.append(("Mentor", answer))
if st.session_state.mentor_chat:
    for who, msg in st.session_state.mentor_chat:
        st.write(f"**{who}:** {msg}")

