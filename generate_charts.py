import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def generate_evaluation_charts():
    # 1. Load the data
    try:
        df = pd.read_csv("rag_evaluation_results.csv")
    except FileNotFoundError:
        print("Error: rag_evaluation_results.csv not found!")
        return

    # 2. Calculate the averages
    summary = df.groupby("strategy")[["context_precision", "context_recall", "faithfulness", "latency_sec"]].mean()
    
    # 3. Setup for the Accuracy Metrics Chart
    metrics = ["Context Precision", "Context Recall", "Faithfulness"]
    standard_scores = summary.loc["standard", ["context_precision", "context_recall", "faithfulness"]].values * 100
    rerank_scores = summary.loc["rerank", ["context_precision", "context_recall", "faithfulness"]].values * 100

    x = np.arange(len(metrics))
    width = 0.35

    # --- CHART 1: ACCURACY METRICS ---
    fig, ax1 = plt.subplots(figsize=(10, 6))
    bars1 = ax1.bar(x - width/2, standard_scores, width, label='Standard RAG', color='#4A90E2')
    bars2 = ax1.bar(x + width/2, rerank_scores, width, label='Reranked RAG (TinyBERT)', color='#F5A623')

    ax1.set_ylabel('Score (%)', fontsize=12, fontweight='bold')
    ax1.set_title('RAG Accuracy Metrics Comparison', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(metrics, fontsize=11)
    ax1.legend()
    ax1.set_ylim(0, 110) # Leave room for labels

    # Add numbers on top of bars
    for bar in bars1 + bars2:
        height = bar.get_height()
        ax1.annotate(f'{height:.1f}%',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    plt.savefig("accuracy_comparison_chart.png", dpi=300)
    print("✅ Saved accuracy chart as 'accuracy_comparison_chart.png'")

    # --- CHART 2: LATENCY TRADE-OFF ---
    fig, ax2 = plt.subplots(figsize=(6, 6))
    strategies = ['Standard RAG', 'Reranked RAG']
    latencies = [summary.loc["standard", "latency_sec"], summary.loc["rerank", "latency_sec"]]

    bars3 = ax2.bar(strategies, latencies, color=['#4A90E2', '#D0021B'], width=0.5)

    ax2.set_ylabel('Average Latency (Seconds)', fontsize=12, fontweight='bold')
    ax2.set_title('Average Response Time per Question', fontsize=14, fontweight='bold')
    ax2.set_ylim(0, max(latencies) + 3)

    for bar in bars3:
        height = bar.get_height()
        ax2.annotate(f'{height:.1f}s',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=11, fontweight='bold')

    plt.tight_layout()
    plt.savefig("latency_comparison_chart.png", dpi=300)
    print("✅ Saved latency chart as 'latency_comparison_chart.png'")

if __name__ == "__main__":
    generate_evaluation_charts()