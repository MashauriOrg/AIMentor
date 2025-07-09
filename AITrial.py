import streamlit as st
import PyPDF2

st.title("PDF Text Extractor")

uploaded_files = st.file_uploader(
    "Upload PDF files (one or more)", type="pdf", accept_multiple_files=True
)

if uploaded_files:
    for file in uploaded_files:
        st.subheader(f"Text from: {file.name}")
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        st.text_area("Extracted Text", value=text[:5000], height=300)
        # (Shows only first 5,000 chars for readability)
