import sys
import os
import json
import time
import requests
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from datasets import Dataset

# Fix legacy module path for Ragas
import langchain_google_vertexai
sys.modules['langchain_community.chat_models.vertexai'] = langchain_google_vertexai

load_dotenv()

from ragas import evaluate
from ragas.run_config import RunConfig
from ragas.metrics import faithfulness, context_precision, context_recall
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# --- Configuration ---
NUM_RUNS = 1                  # Set to 1 for a stable pass; run again if capturing multi-run variance
API_URL = "http://localhost:8000/chat"
SESSION_ID = 999999

# --- Initialize Evaluator Models (No temperature parameter to eliminate warnings) ---
eval_llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash")
eval_embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

# Fast 40s timeout and single worker to protect free-tier quotas
eval_run_config = RunConfig(max_workers=1, timeout=40, max_retries=2)


def run_pipeline_evaluation(strategy_name: str, dataset: list) -> pd.DataFrame:
    print(f"\n=======================================================")
    print(f"🚀 COLLECTING CHAT RESPONSES: {strategy_name.upper()}")
    print(f"=======================================================")

    results = {
        "question": [],
        "answer": [],
        "contexts": [],
        "ground_truth": [],
        "latency_sec": []
    }

    # Step 1: Collect responses from FastAPI
    for i, item in enumerate(dataset):
        question = item["question"]
        print(f"[{i+1}/{len(dataset)}] Querying {strategy_name.upper()}: {question[:45]}...")

        start_time = time.time()
        try:
            resp = requests.post(API_URL, json={
                "session_id": SESSION_ID,
                "question": question,
                "strategy": strategy_name
            }, timeout=60)
            latency = time.time() - start_time

            if resp.status_code == 200:
                data = resp.json()
                results["question"].append(question)
                results["answer"].append(data.get("answer", ""))
                results["contexts"].append(data.get("context_chunks", []))
                results["ground_truth"].append(item["ground_truth_answer"])
                results["latency_sec"].append(latency)
            else:
                print(f"   ⚠️ HTTP {resp.status_code} on Q{i+1}")
        except Exception as e:
            print(f"   ⚠️ Request failed on Q{i+1}: {e}")

        # Pacing delay between chat questions
        time.sleep(2)

    print(f"\n✅ Finished collecting responses for {strategy_name.upper()}.")
    print("⏳ Cooling down for 30s before starting Ragas automated grading...")
    time.sleep(30)

    # Step 2: Grade with Ragas in small chunks of 15 to prevent rate limits
    chunk_size = 15
    graded_dfs = []
    total_items = len(results["question"])

    for start_idx in range(0, total_items, chunk_size):
        end_idx = min(start_idx + chunk_size, total_items)
        print(f"\n📊 Grading batch [{start_idx + 1} to {end_idx}] of {total_items} with Ragas...")

        sub_dict = {
            "question": results["question"][start_idx:end_idx],
            "answer": results["answer"][start_idx:end_idx],
            "contexts": results["contexts"][start_idx:end_idx],
            "ground_truth": results["ground_truth"][start_idx:end_idx],
        }

        sub_dataset = Dataset.from_dict(sub_dict)

        try:
            eval_res = evaluate(
                dataset=sub_dataset,
                metrics=[context_precision, context_recall, faithfulness],
                llm=eval_llm,
                embeddings=eval_embeddings,
                run_config=eval_run_config
            )
            sub_df = eval_res.to_pandas()
            sub_df["latency_sec"] = results["latency_sec"][start_idx:end_idx]
            graded_dfs.append(sub_df)
        except Exception as e:
            print(f"   ⚠️ Ragas grading exception in batch: {e}")

        # Cooldown between Ragas batches
        if end_idx < total_items:
            print("   ⏳ Pausing 45s to reset Gemini API rate quotas...")
            time.sleep(45)

    final_strategy_df = pd.concat(graded_dfs, ignore_index=True) if graded_dfs else pd.DataFrame()
    final_strategy_df["strategy"] = strategy_name
    return final_strategy_df


def main():
    try:
        with open("ground_truth.json", "r") as f:
            test_dataset = json.load(f)
    except FileNotFoundError:
        print("Error: ground_truth.json not found.")
        return

    print(f"Loaded {len(test_dataset)} benchmark questions.")

    # 1. Run Standard Pipeline
    standard_df = run_pipeline_evaluation("standard", test_dataset)

    print("\n⏳ Pausing 60s between pipelines to ensure fresh quotas...")
    time.sleep(60)

    # 2. Run Rerank Pipeline
    rerank_df = run_pipeline_evaluation("rerank", test_dataset)

    # 3. Save Clean Combined Output
    final_df = pd.concat([standard_df, rerank_df], ignore_index=True)
    final_df.to_csv("rag_evaluation_results.csv", index=False)

    print("\n🎉 EVALUATION COMPLETE! 🎉")
    print("Results successfully saved to: rag_evaluation_results.csv")

    metrics = ["context_precision", "context_recall", "faithfulness", "latency_sec"]
    summary = final_df.groupby("strategy")[metrics].mean()
    print("\n--- SUMMARY METRICS ---")
    print(summary)


if __name__ == "__main__":
    main()