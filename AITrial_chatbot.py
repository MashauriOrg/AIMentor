import streamlit as st
import openai
import os
import traceback

st.title("AI Mentor Bot")

client = openai.OpenAI()

# Always initialize chat history
if "history" not in st.session_state:
    st.session_state["history"] = [
        {"role": "system", "content": "You are an experienced entrepreneurial mentor helping a student team. Be friendly, supportive, and practical in your advice."}
    ]

# --- Use a Streamlit form to handle input safely ---
with st.form(key="chat_form"):
    user_message = st.text_input("You:", key="user_input")
    submitted = st.form_submit_button("Send")

if submitted and user_message:
    st.session_state["history"].append({"role": "user", "content": user_message})

    try:
        MAX_HISTORY = 20
        trimmed_history = [st.session_state["history"][0]] + st.session_state["history"][-MAX_HISTORY:]

        # Debug info (optional)
        print("Submitting prompt to OpenAI:", user_message)
        print("Using API key:", os.getenv("OPENAI_API_KEY"))
        print("Using model: gpt-4o")
        print("Trimmed history:", trimmed_history)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=trimmed_history,
            timeout=15,
        )
        ai_reply = response.choices[0].message.content
        st.session_state["history"].append({"role": "assistant", "content": ai_reply})
        st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")
        print("Error:", e)
        traceback.print_exc()

# Button to clear the chat history and reset the app
if st.button("Clear Chat"):
    del st.session_state["history"]
    st.rerun()

# Display the chat history (skip system message)
for msg in st.session_state["history"][1:]:
    if msg["role"] == "user":
        st.write(f"**You:** {msg['content']}")
    else:
        st.write(f"**Mentor Bot:** {msg['content']}")
