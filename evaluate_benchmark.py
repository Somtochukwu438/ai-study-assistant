import sys
import langchain_google_vertexai
# THE FIX: Trick Ragas into finding the moved VertexAI module
sys.modules['langchain_community.chat_models.vertexai'] = langchain_google_vertexai

import json
import time
import requests
import pandas as pd
from datasets import Dataset
import os
from dotenv import load_dotenv
load_dotenv()

# Ragas and LangChain imports for grading
from ragas import evaluate
from ragas.run_config import RunConfig
from ragas.metrics import faithfulness, context_precision, context_recall
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# 1. Configure Gemini to act as the "Judge" for our metrics
eval_llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash")
eval_embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

# Throttle Ragas so it doesn't blow past rate limits
eval_run_config = RunConfig(max_workers=1, timeout=180)

# 2. Setup API Endpoint
API_URL = "http://localhost:8000/chat"
SESSION_ID = 999999  # Dummy session ID

def run_pipeline_evaluation(strategy_name, dataset):
    print(f"\n🚀 Starting batch evaluation for strategy: {strategy_name.upper()}")

    results = {
        "question": [],
        "answer": [],
        "contexts": [],
        "ground_truth": [],
        "latency_sec": []
    }

    for i, item in enumerate(dataset):
        print(f"   Processing question {i+1}/{len(dataset)}...")
        question = item["question"]

        start_time = time.time()

        response = requests.post(API_URL, json={
            "session_id": SESSION_ID,
            "question": question,
            "strategy": strategy_name
        }, timeout=120)

        # Prevent flooding the API back-to-back
        time.sleep(2)

        latency = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            retrieved_contexts = data.get("context_chunks", [])

            results["question"].append(question)
            results["answer"].append(data["answer"])
            results["contexts"].append(retrieved_contexts)
            results["ground_truth"].append(item["ground_truth_answer"])
            results["latency_sec"].append(latency)
        else:
            print(f"   ❌ Error on question {i+1}: Backend returned {response.status_code}")

    print(f"✅ {strategy_name.upper()} data collection complete. Grading with Ragas...")

    hf_dataset = Dataset.from_dict(results)

    evaluation_result = evaluate(
        dataset=hf_dataset,
        metrics=[context_precision, context_recall, faithfulness],
        llm=eval_llm,
        embeddings=eval_embeddings,
        run_config=eval_run_config
    )

    df = evaluation_result.to_pandas()
    df["latency_sec"] = results["latency_sec"]
    df["strategy"] = strategy_name

    return df

def main():
    try:
        with open("ground_truth.json", "r") as f:
            test_dataset = json.load(f)
    except FileNotFoundError:
        print("Error: ground_truth.json not found in this directory.")
        return

    # Run the Standard Pipeline
    standard_df = run_pipeline_evaluation(strategy_name="standard", dataset=test_dataset)

    # Run the Rerank Pipeline
    rerank_df = run_pipeline_evaluation(strategy_name="rerank", dataset=test_dataset)

    # Merge and save
    final_df = pd.concat([standard_df, rerank_df], ignore_index=True)
    final_df.to_csv("rag_evaluation_results.csv", index=False)

    print("\n🎉 EVALUATION COMPLETE! 🎉")
    print("Results saved to: rag_evaluation_results.csv")

    print("\n--- PERFORMANCE SUMMARY ---")
    summary = final_df.groupby("strategy")[["context_precision", "context_recall", "faithfulness", "latency_sec"]].mean()
    print(summary)

if __name__ == "__main__":
    main()