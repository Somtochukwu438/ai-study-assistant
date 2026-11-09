```markdown
# Chat-with-your-Notes: An Empirical Evaluation of Retrieval Strategies in Educational RAG Systems

**Author:** Somtochukwu "Augustus" Nwanno  
**Advisor:** Dr. Ning Zhang  
**Course:** Senior Seminar / Capstone Project  
**Repository:** [github.com/Somtochukwu438/ai-study-assistant](https://github.com/Somtochukwu438/ai-study-assistant)

---

## 📌 Project Overview
**Chat-with-your-Notes** is an educational Retrieval-Augmented Generation (RAG) platform designed to provide strictly grounded question-answering and self-assessment quiz generation over uploaded course lecture notes and academic papers. 

The primary research objective of this capstone is to empirically evaluate the trade-offs between **Bi-Encoder Dense Vector Search (Pipeline A)** and **Cross-Encoder Reranking (Pipeline B)** regarding retrieval precision, hallucination prevention, and response latency.

---

## 🏛️ System Architecture

The application implements a dual-pipeline retrieval architecture toggleable in real time:


```

User Query ──► [FastAPI Backend]
│
┌───────────┴───────────┐
▼                       ▼
[Pipeline A: Standard]    [Pipeline B: Reranked]
│                       │
ChromaDB Vector Search      ChromaDB Initial Candidate Pool
(Top k=3)                      (Top k=10)
│                       │
│             TinyBERT Cross-Encoder Scoring
│             (cross-encoder/ms-marco-TinyBERT-L-2-v2)
│                       │
│                  Reranked Top 3
└───────────┬───────────┘
▼
Strict Negative Guardrail
(Prompt Rejection Directive)
│
▼
Gemini 3.8 Flash (LLM)
│
▼
Grounded Response + Exact Page Citations

```

### Retrieval Strategies Compared
1. **Pipeline A (Standard Vector Search):** Uses Google GenAI embeddings (`gemini-embedding-001`) with ChromaDB cosine similarity search to retrieve the top $k=3$ chunks directly.
2. **Pipeline B (Two-Stage Cross-Encoder Reranking):** Fetches an expanded candidate pool of $k=10$ chunks from ChromaDB, scores all pairs through `cross-encoder/ms-marco-TinyBERT-L-2-v2`, and feeds the top 3 highest-scoring passages to the LLM.

---

## 🛠️ Tech Stack

* **Backend:** FastAPI (Python 3.13), Uvicorn, LangChain, Pydantic
* **Frontend:** React, Vite, Tailwind CSS, Lucide Icons
* **Vector Store & Embeddings:** ChromaDB, `models/gemini-embedding-001`
* **Reranker:** Sentence-Transformers (`cross-encoder/ms-marco-TinyBERT-L-2-v2`)
* **Generative & Evaluation LLM:** Google GenAI (`gemini-3.8-flash`)
* **Evaluation Frameworks:** Ragas, Pandas, Datasets, Scipy

---

## 📊 Empirical Evaluation & Benchmark Results

The system was evaluated using a customized 45-question benchmark dataset (`ground_truth.json`), incorporating 30 factual/reasoning queries and 15 adversarial, out-of-scope unanswerable queries to test hallucination resistance.

### Repeated Trial Summary ($N=5$ Trials)

| Metric | Pipeline A (Standard $k=3$) | Pipeline B (Reranked $k=10 \rightarrow 3$) | Delta / Gain |
| :--- | :---: | :---: | :---: |
| **Context Precision** | $80.1\% \pm 1.2\%$ | **$85.2\% \pm 0.9\%$** | **$+5.1\%$** |
| **Answer Faithfulness** | $76.5\% \pm 2.1\%$ | **$89.1\% \pm 1.3\%$** | **$+12.6\%$** |
| **Hallucination Rate** | $11.1\%$ | **$0.0\%$** | **$-11.1\%$** |
| **Mean Latency** | **$4.15\text{ s} \pm 0.45\text{ s}$** | $8.92\text{ s} \pm 0.30\text{ s}$ | $+4.77\text{ s}$ |

### Key Experimental Insights
1. **Recall Rescue:** Cross-encoder reranking rescues relevant passages buried at candidate ranks 4–10 (e.g., retrieving Alain Locke's author attribution for *"Enter the New Negro"* from Page 7), converting retrieval misses into grounded answers.
2. **Negative Guardrailing:** Hardened negative rejection directives in `main.py` force the system to return *"I cannot answer this based on the provided notes."* when context is missing, completely preventing pre-trained parametric leakage on out-of-scope queries.
3. **Manual Judge Validation:** A 20% stratified human-in-the-loop audit documented in `manual_judge_audit.md` demonstrated **88.9% concordance** with automated Ragas grading standards.

---

## 📂 Repository File Structure


```

ai-study-assistant/
├── main.py                     # FastAPI server, RAG pipelines, /chat & /quiz endpoints
├── evaluate_benchmark.py       # Multi-run evaluation benchmark harness
├── ground_truth.json           # 45-question ground-truth evaluation dataset
├── annotation_guidelines.md    # Formal ground-truth annotation rubric
├── manual_judge_audit.md       # 20% stratified manual human validation audit
├── rag_evaluation_results.csv  # Granular empirical evaluation output logs
├── ingest.py                   # PDF text extraction and ChromaDB chunking script
├── requirements.txt            # Pinned Python package dependencies
└── frontend/                   # React + Vite web user interface

```

---

## 🚀 Quickstart & Setup Guide

### 1. Prerequisites
* Python 3.11+
* Node.js 18+ and npm
* Google Gemini API Key

### 2. Clone the Repository
```bash
git clone [https://github.com/Somtochukwu438/ai-study-assistant.git](https://github.com/Somtochukwu438/ai-study-assistant.git)
cd ai-study-assistant

```

### 3. Backend Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

```

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY="your-google-api-key"

```

Start the FastAPI server:

```bash
uvicorn main:app --reload

```

The backend will run on `http://localhost:8000`.

### 4. Frontend Setup

In a new terminal window:

```bash
cd frontend
npm install
npm run dev

```

Open `http://localhost:5173` in your browser.

### 5. Running the Automated Benchmark

To run the evaluation script across the 45-question ground-truth dataset:

```bash
python evaluate_benchmark.py

```

Outputs and metrics will be recorded in `rag_evaluation_results.csv`.

---

## 📜 Research Documentation

* **Annotation Rubric:** See [`annotation_guidelines.md`](https://www.google.com/search?q=annotation_guidelines.md) for criteria on reference answer and passage bounding.
* **Validation Audit:** See [`manual_judge_audit.md`](https://www.google.com/search?q=manual_judge_audit.md) for the human-versus-Ragas concordance analysis.

```

```
