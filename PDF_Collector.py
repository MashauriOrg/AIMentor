import streamlit as st
import PyPDF2
import os

st.set_page_config(page_title="PDF Collector")

st.title("PDF Collector - Store Extracted Book Texts")

uploaded_files = st.file_uploader("Choose PDF books to load", accept_multiple_files=True, type="pdf")

# Directory to save extracted text files
output_dir = "extracted_books"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

book_texts = {}

if uploaded_files:
    for file in uploaded_files:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        book_texts[file.name] = text
        # Save to .txt file
        txt_file_path = os.path.join(output_dir, file.name.replace(".pdf", ".txt"))
        with open(txt_file_path, "w", encoding="utf-8") as f:
            f.write(text)
        st.subheader(f"File: {file.name}")
        st.write(f"Extracted {len(text):,} characters.")
        st.text_area("Preview:", value=text[:500], height=150)
        st.write("---")

    st.success(f"Loaded {len(book_texts)} books into memory and saved as .txt files.")
    st.write("Books loaded and saved:", list(book_texts.keys()))
