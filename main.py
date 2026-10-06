import os
import shutil
from datetime import datetime
from typing import List, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, File, UploadFile, Depends
from pydantic import BaseModel, Field
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from flashrank import Ranker, RerankRequest
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship

load_dotenv()

app = FastAPI(title="Study Assistant API")
CHROMA_PATH = "chroma_db"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. Database Setup (SQLite + SQLAlchemy) ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./chat_history.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DBSession(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)
    messages = relationship("DBMessage", back_populates="session", cascade="all, delete-orphan")

class DBMessage(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    role = Column(String)  # "user" or "assistant"
    text = Column(Text)
    sources = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    session = relationship("DBSession", back_populates="messages")

Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 2. Initialize AI Models ---
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0)
ranker = Ranker(model_name="ms-marco-TinyBERT-L-2-v2", cache_dir="./model_cache")
# --- 3. Prompts ---
PROMPT_TEMPLATE = """
You are an expert study assistant. Answer the user's question using ONLY the provided context.
If the answer is not contained in the context, say "I cannot answer this based on the provided notes."

Context:
{context}

Question:
{question}
"""
prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

# --- 4. Pydantic Schemas ---
class QueryRequest(BaseModel):
    session_id: Optional[int] = None
    question: str
    strategy: Optional[str] = "standard"

class QuizOption(BaseModel):
    text: str = Field(description="The text of the multiple choice option")
    is_correct: bool = Field(description="True if this is the correct answer, False otherwise")

class QuizQuestion(BaseModel):
    question: str = Field(description="The multiple choice question")
    options: List[QuizOption] = Field(description="Exactly 4 possible answers")
    explanation: str = Field(description="A brief explanation of why the correct answer is right")

class Quiz(BaseModel):
    questions: List[QuizQuestion]

class QuizRequest(BaseModel):
    topic: str
    num_questions: int = 3

def extract_text(content) -> str:
    if isinstance(content, str): return content
    if isinstance(content, list) and len(content) > 0 and isinstance(content[0], dict) and "text" in content[0]: return content[0]["text"]
    return str(content)

# --- 5. Session Endpoints ---
@app.post("/sessions")
def create_session(db_session: Session = Depends(get_db)):
    new_session = DBSession(title="New Chat")
    db_session.add(new_session)
    db_session.commit()
    db_session.refresh(new_session)
    return {"id": new_session.id, "title": new_session.title}

@app.get("/sessions")
def get_sessions(db_session: Session = Depends(get_db)):
    sessions = db_session.query(DBSession).order_by(DBSession.created_at.desc()).all()
    return [{"id": s.id, "title": s.title} for s in sessions]

@app.get("/sessions/{session_id}/messages")
def get_messages(session_id: int, db_session: Session = Depends(get_db)):
    messages = db_session.query(DBMessage).filter(DBMessage.session_id == session_id).order_by(DBMessage.created_at.asc()).all()
    return [{"role": m.role, "text": m.text, "sources": m.sources} for m in messages]

@app.delete("/sessions/{session_id}")
def delete_session(session_id: int, db_session: Session = Depends(get_db)):
    session = db_session.query(DBSession).filter(DBSession.id == session_id).first()
    if session:
        db_session.delete(session)
        db_session.commit()
    return {"message": "Session deleted"}

# --- 6. Core Query & Task Endpoints ---
@app.post("/chat")
def chat_endpoint(request: QueryRequest, db_session: Session = Depends(get_db)):
    session = None
    if request.session_id is not None:
        session = db_session.query(DBSession).filter(DBSession.id == request.session_id).first()
        if session:
            # Update title if it is the first question in the session
            if session.title == "New Chat":
                session.title = (request.question[:25] + '...') if len(request.question) > 25 else request.question
                db_session.commit()
            
            # Save user question
            user_msg = DBMessage(session_id=session.id, role="user", text=request.question)
            db_session.add(user_msg)
            db_session.commit()

    # Perform RAG Retrieval
    initial_k = 10 if request.strategy == "rerank" else 3
    retrieved_docs = db.similarity_search(request.question, k=initial_k)
    
    if not retrieved_docs:
        if session:
            assistant_msg = DBMessage(session_id=session.id, role="assistant", text="No matching documents found.")
            db_session.add(assistant_msg)
            db_session.commit()
        return {
            "answer": "No matching documents found.",
            "sources": [],
            "context_chunks": [],
            "strategy_used": request.strategy
        }

    if request.strategy == "rerank":
        passages = [{"id": i, "text": doc.page_content, "meta": doc.metadata} for i, doc in enumerate(retrieved_docs)]
        reranked_results = ranker.rerank(RerankRequest(query=request.question, passages=passages))[:3]
        context_chunks = [r["text"] for r in reranked_results]
        context_text = "\n\n---\n\n".join(context_chunks)
        sources = [f"Page {r['meta'].get('page')}" for r in reranked_results]
    else:
        context_chunks = [doc.page_content for doc in retrieved_docs]
        context_text = "\n\n---\n\n".join(context_chunks)
        sources = [f"Page {doc.metadata.get('page')}" for doc in retrieved_docs]

    # Generate answer with Gemini
    chain = prompt | llm
    raw_response = chain.invoke({"context": context_text, "question": request.question})
    clean_answer = extract_text(raw_response.content)
    unique_sources = list(set(sources))

    # Save assistant response to DB if session exists
    if session:
        ai_msg = DBMessage(session_id=session.id, role="assistant", text=clean_answer, sources=unique_sources)
        db_session.add(ai_msg)
        db_session.commit()

    return {
        "answer": clean_answer,
        "sources": unique_sources,
        "context_chunks": context_chunks,
        "strategy_used": request.strategy
    }

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    os.makedirs("data", exist_ok=True)
    temp_path = f"data/{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    loader = PyPDFLoader(temp_path)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, separators=["\n\n", "\n", " ", ""])
    chunks = text_splitter.split_documents(documents)
    
    db.add_documents(chunks)
    return {"message": f"Successfully ingested {file.filename}", "pages_processed": len(documents), "chunks_added": len(chunks)}

@app.post("/quiz")
def generate_quiz(request: QuizRequest):
    retrieved_docs = db.similarity_search(request.topic, k=5)
    if not retrieved_docs: 
        raise HTTPException(status_code=404, detail="No notes found for this topic.")
        
    context_text = "\n\n---\n\n".join([doc.page_content for doc in retrieved_docs])
    QUIZ_PROMPT = """You are an expert professor. Based ONLY on the provided context, generate a multiple-choice quiz about {topic} with exactly {num_questions} questions. Each question must have exactly 4 options, with only one correct answer. Context: {context}"""
    quiz_prompt_template = ChatPromptTemplate.from_template(QUIZ_PROMPT)
    
    structured_llm = llm.with_structured_output(Quiz)
    chain = quiz_prompt_template | structured_llm
    return chain.invoke({"topic": request.topic, "num_questions": request.num_questions, "context": context_text})