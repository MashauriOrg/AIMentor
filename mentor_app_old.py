import streamlit as st
import openai, os
from langchain.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI

# --- Config & Auth ---
openai.api_key = os.getenv("OPENAI_API_KEY")
st.set_page_config(page_title="AI Mentor", layout="centered")

# --- Load Vector Index for retrieval ---
vectorstore = FAISS.load_local("faiss_index", OpenAIEmbeddings())

# --- Build a RAG Chain: Retrieval + Chat w/ memory ---
llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
chain = ConversationalRetrievalChain.from_llm(
    llm,
    retriever=vectorstore.as_retriever(search_kwargs={"k":3}),
    condense_question_prompt="""You are a wise mentor... condense the follow-up question: {question}""",
    response_prompt="""You are a wise mentor with decades of experience...
    Review your book library first, then answer Socratically: {context}""",
)

# --- Team login ---
if "team" not in st.session_state:
    team = st.text_input("Team name", key="team_name")
    pw   = st.text_input("Password", type="password", key="team_pw")
    if st.button("Login"):
        # replace with your real check
        if pw == "letmein":  
            st.session_state.team = team
            st.experimental_rerun()
        else:
            st.error("Invalid creds")
    st.stop()

st.title(f"👥 Team {st.session_state.team} — Your AI Mentor")

# --- Conversation memory ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- User input form ---
with st.form("msg_form", clear_on_submit=True):
    query = st.text_input("Ask your mentor…")
    submitted = st.form_submit_button("Send")

if submitted and query:
    result = chain({"question": query, "chat_history": st.session_state.chat_history})
    st.session_state.chat_history.append((query, result["answer"]))

# --- Display history ---
for user_msg, bot_msg in st.session_state.chat_history:
    st.markdown(f"**You:** {user_msg}")
    st.markdown(f"**Mentor:** {bot_msg}")
