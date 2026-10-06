import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

# 1. Load the hidden API key from the .env file
load_dotenv()

FILE_PATH = "data/sample.pdf"
CHROMA_PATH = "chroma_db" # The folder where our database will be saved

def main():
    print(f"Loading {FILE_PATH}...")
    loader = PyPDFLoader(FILE_PATH)
    documents = loader.load()

    print("Splitting text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Generated {len(chunks)} chunks.")

    # 2. Initialize the Gemini embedding model
    print("Initializing Gemini embeddings...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    # 3. Create the vector database and save it locally
    print(f"Saving to ChromaDB at ./{CHROMA_PATH}...")
    db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )
    
    print("✅ Database successfully built and saved!")

if __name__ == "__main__":
    main()