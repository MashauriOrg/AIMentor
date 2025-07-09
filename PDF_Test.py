import streamlit as st
import PyPDF2

st.title("PDF Upload Test")

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
if uploaded_file is not None:
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    st.write("Extracted Text (first 1000 characters):")
    st.write(text[:1000])  # Show only first 1000 chars for test
