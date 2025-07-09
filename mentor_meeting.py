import streamlit as st
import os

# --- Settings ---
SCRIPT_FOLDER = "meeting_scripts"

TEAM_PASSWORDS = {
    "Team Alpha": "alpha123",
    "Team Beta": "beta456",
    "Team Gamma": "gamma789",
    # Add more teams here!
}

# --- Helpers ---
def get_meeting_scripts():
    return [f for f in os.listdir(SCRIPT_FOLDER) if f.endswith('.txt')]

def next_step():
    st.session_state.step += 1

def prev_step():
    if st.session_state.step > 0:
        st.session_state.step -= 1

# --- Main App ---

st.set_page_config(page_title="AI Mentor Meeting")
st.title("🤖 AI Mentor - Team Meeting")

# 1. Team selection and password
team_names = list(TEAM_PASSWORDS.keys())
team = st.selectbox("Select your team:", team_names)
password = st.text_input("Team password:", type="password")
if password != TEAM_PASSWORDS[team]:
    st.warning("Enter the correct password for your team to proceed.")
    st.stop()

st.success(f"Welcome, {team}! Let's start your session.")

# 2. Meeting script selection
scripts = get_meeting_scripts()
if not scripts:
    st.error("No meeting scripts found! Add .txt files to the meeting_scripts/ folder.")
    st.stop()
script_file = st.selectbox("Choose your meeting:", scripts)

# 3. Load script and initialize session state
with open(os.path.join(SCRIPT_FOLDER, script_file), "r") as f:
    lines = [l.strip() for l in f.readlines() if l.strip()]

if "step" not in st.session_state:
    st.session_state.step = 0
if "inputs" not in st.session_state:
    st.session_state.inputs = []
if "members" not in st.session_state:
    st.session_state.members = []
if "member_index" not in st.session_state:
    st.session_state.member_index = 0

step = st.session_state.step

# --- Main loop ---
while step < len(lines):
    content = lines[step]
    # --- Multi-member entry block ---
    if content.startswith("ENTER_TEAM_MEMBERS"):
        # Assume previous step asked for number of members
        num_members = st.session_state.inputs[-1] if st.session_state.inputs else 1
        try:
            num_members = int(num_members)
        except:
            num_members = 1

        idx = st.session_state.member_index

        if idx < num_members:
            key_prefix = f"member_{idx}_"
            name = st.session_state.get(key_prefix + "name", "")
            email = st.session_state.get(key_prefix + "email", "")
            reason = st.session_state.get(key_prefix + "reason", "")
            objective = st.session_state.get(key_prefix + "objective", "")

            st.subheader(f"Team Member {idx+1}")
            name = st.text_input("Full name", value=name, key=key_prefix + "name")
            email = st.text_input("Email", value=email, key=key_prefix + "email")
            reason = st.text_area("Why do you want to work on this problem?", value=reason, key=key_prefix + "reason")
            objective = st.text_area("Your objective for being part of the team/USSAVI project?", value=objective, key=key_prefix + "objective")

            col1, col2 = st.columns([1,1])
            if col1.button("Save Member", key=f"save_{idx}"):
                st.session_state.members.append({
                    "Name": name,
                    "Email": email,
                    "Reason": reason,
                    "Objective": objective,
                })
                st.session_state.member_index += 1
                # Remove keys for next round (avoids overwrite)
                for k in ["name", "email", "reason", "objective"]:
                    st.session_state.pop(key_prefix + k, None)
                st.rerun()
            if col2.button("Back", key=f"back_{step}_{idx}"):
                if idx > 0:
                    st.session_state.member_index -= 1
                    st.session_state.members.pop()
                    # Remove keys for previous member
                    prev_prefix = f"member_{st.session_state.member_index}_"
                    for k in ["name", "email", "reason", "objective"]:
                        st.session_state.pop(prev_prefix + k, None)
                    st.rerun()
            break  # Don't advance to next step yet
        else:
            st.write("All members entered!")
            for i, m in enumerate(st.session_state.members, 1):
                st.markdown(f"**{i}. {m['Name']}** — {m['Email']}  \n_Reason_: {m['Reason']}  \n_Objective_: {m['Objective']}")
            if st.button("Continue to next step"):
                st.session_state.member_index = 0
                next_step()
                st.rerun()
            break
    # --- Standard script logic ---
    elif content.lower().startswith("step"):
        st.subheader(content)
        if st.button("Next", key=f"next_{step}"):
            next_step()
            st.rerun()
        if step > 0 and st.button("Back", key=f"back_{step}"):
            prev_step()
            st.rerun()
        break
    elif content.endswith(":"):
        user_input = st.text_input(content, key=f"input_{step}")
        if st.button("Save & Next", key=f"save_next_{step}"):
            st.session_state.inputs.append(user_input)
            next_step()
            st.rerun()
        if step > 0 and st.button("Back", key=f"back_{step}"):
            prev_step()
            st.rerun()
        break
    else:
        st.markdown(content)
        if st.button("Next", key=f"next_{step}"):
            next_step()
            st.rerun()
        if step > 0 and st.button("Back", key=f"back_{step}"):
            prev_step()
            st.rerun()
        break

if step >= len(lines):
    st.success("Meeting complete! Thanks for participating.")
    st.write("Your session inputs:")
    for i, inp in enumerate(st.session_state.inputs, 1):
        st.write(f"{i}. {inp}")
    if st.session_state.members:
        st.write("Team Members Entered:")
        for i, m in enumerate(st.session_state.members, 1):
            st.markdown(f"**{i}. {m['Name']}** — {m['Email']}  \n_Reason_: {m['Reason']}  \n_Objective_: {m['Objective']}")
