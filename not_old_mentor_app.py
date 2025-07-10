# mentor_app.py

import os
import streamlit as st
import openai

# --- Community imports to avoid the Pydantic .get bug ---
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import LLMChain, ConversationalRetrievalChain


# PromptTemplate is still in core
from langchain.prompts import PromptTemplate

# --- Config & Auth ---
openai.api_key = os.getenv("OPENAI_API_KEY")
st.set_page_config(page_title="AI Mentor", layout="centered")

# --- Load Vector Index for retrieval ---
embeddings = OpenAIEmbeddings(openai_api_key=openai.api_key)
vectorstore = FAISS.load_local(
    "faiss_index",
    embeddings,
    allow_dangerous_deserialization=True
)

# --- Prompt templates for the chain ---
condense_template = PromptTemplate(
    input_variables=["question"],
    template=(
        "You are a wise mentor. "
        "Condense the follow-up question for clarity:\n\n"
        "{question}"
    )
)

response_template = PromptTemplate(
    input_variables=["context"],
    template=(
        "You are a wise mentor with decades of experience assisting young entrepreneurs. "
        "First review your curated book library for relevant passages, then respond in a Socratic style:\n\n"
        "{context}"
    )
)

# --- Build sub-chains explicitly ---
llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

question_gen_chain = LLMChain(
    llm=llm,
    prompt=condense_template
)

combine_docs_chain = LLMChain(
    llm=llm,
    prompt=response_template
)

chain = ConversationalRetrievalChain(
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
    question_generator=question_gen_chain,
    combine_docs_chain=combine_docs_chain,
    return_source_documents=False,
)

# --- Team login ---
if "team" not in st.session_state:
    team = st.text_input("Team name", key="team_name")
    pw   = st.text_input("Password", type="password", key="team_pw")
    if st.button("Login"):
        if pw == "letmein":
            st.session_state.team = team
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

st.title(f"👥 Team '{st.session_state.team}' — Your AI Mentor")

# --- Conversation memory ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- User input form ---
with st.form("msg_form", clear_on_submit=True):
    query = st.text_input("Ask your mentor…")
    submitted = st.form_submit_button("Send")

if submitted and query:
    result = chain({
        "question": query,
        "chat_history": st.session_state.chat_history
    })
    st.session_state.chat_history.append((query, result["answer"]))

# --- Display history ---
for user_msg, bot_msg in st.session_state.chat_history:
    st.markdown(f"**You:** {user_msg}")
    st.markdown(f"**Mentor:** {bot_msg}")
