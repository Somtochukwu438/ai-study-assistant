import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Load API key
load_dotenv()

CHROMA_PATH = "chroma_db"

def main():
    # 1. Initialize the exact same embedding model we used to save the data
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

    # 2. Connect to our saved database
    print("Connecting to ChromaDB...")
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)

    # 3. Define our test question
    query_text = "What is the significance of Mansa Musa and the Mali Empire?"
    print(f"\nSearching database for: '{query_text}'\n")

    # 4. Perform a similarity search and get the top 3 results with their scores
    results = db.similarity_search_with_score(query_text, k=3)

    # 5. Print out the results
    print("--- TOP 3 MATCHES ---\n")
    for i, (doc, score) in enumerate(results):
        print(f"Result {i+1} (Relevance Score: {score:.4f})")
        print(f"Source: Page {doc.metadata.get('page')} of {doc.metadata.get('source')}")
        print(f"Text: {doc.page_content}")
        print("-" * 40 + "\n")

if __name__ == "__main__":
    main()