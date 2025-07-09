import streamlit as st
import PyPDF2

st.set_page_config(page_title="PDF Multi-Uploader")

st.title("PDF Multi-Uploader")

# Let user upload multiple PDF files
uploaded_files = st.file_uploader("Choose one or more PDF files", accept_multiple_files=True, type="pdf")

if uploaded_files:
    for file in uploaded_files:
        st.subheader(f"File: {file.name}")
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        st.text_area("Extracted text (first 1000 chars):", value=text[:1000], height=200)
        st.write("---")
