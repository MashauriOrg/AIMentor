# AIMentor

This project provides a Streamlit application acting as an AI mentor for entrepreneurship teams. It relies on a local library of book excerpts as the primary knowledge source.

## Setup

1. Place plain text book files in `extracted_books/`.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set the `OPENAI_API_KEY` environment variable.

## Building the Book Index

Run the ingestion script to create embeddings and a FAISS index:

```bash
python ingest_books.py
```

This generates `faiss_index/index.faiss` and `faiss_index/texts.npy`. The directory is ignored by Git and must exist locally before running the app.

## Running the App

Start Streamlit:

```bash
streamlit run mentor_app.py
```

When a user sends a message, the app searches the FAISS index for relevant book excerpts and injects them into the conversation context so answers reference the book library before looking elsewhere.
## Persistent FAISS Index on Render

Our app uses a large FAISS index file (`index.faiss`) to power fast, AI-based search. Because GitHub won’t accept such big binaries, we now keep this index on a mounted disk in our Render service instead of in our code repo.

### How it works

1. **Persistent Disk on Render**  
   We attached a small SSD volume to our Render web service (mounted at `/mnt/data/faiss_index`).  
   - The FAISS index file lives here permanently, across every deploy.  
   - We copied `index.faiss` up to `/mnt/data/faiss_index/index.faiss` once by secure‐copy (scp).  

2. **Environment Variable for the Path**  
   In order to keep the code the same locally and on Render, we added an environment variable:
   ```bash
   FAISS_INDEX_PATH=/mnt/data/faiss_index/index.faiss
