import sys
import types

# --- QUICK FIX FOR RAGAS BUG ---
# Ragas crashes looking for an old VertexAI file that LangChain deleted.
# We create a fake, empty module to trick it into loading successfully!
dummy_chat = types.ModuleType("langchain_community.chat_models.vertexai")
dummy_chat.ChatVertexAI = type("ChatVertexAI", (object,), {})
sys.modules["langchain_community.chat_models.vertexai"] = dummy_chat
# -------------------------------

import os
from dotenv import load_dotenv
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, context_precision
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
import pandas as pd

load_dotenv()

# 1. Initialize Gemini to act as the "Judge"
eval_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest")
eval_embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

# 2. Hardcode the test data from your previous API test
data = {
    "question": ["What is the significance of Mansa Musa?"],
    "answer": ["Based on the provided notes, the significance of Mansa Musa includes representation of African power and wealth. He controlled a massive West African empire built on the gold and salt trade."],
    "contexts": [["I start with Mansa Musa, the 14th-century ruler of the Mali Empire, because he reminds me that African history before slavery was powerful, wealthy, and educated. Mansa Musa controlled a huge West African empire built on gold and salt trade, and historians describe him as one of the wealthiest rulers in world history."]],
    "ground_truth": ["Mansa Musa represents African power, wealth, and education prior to slavery. He controlled a massive empire built on gold and salt, and put West Africa on the global map."]
}

# Convert to a HuggingFace Dataset
dataset = Dataset.from_dict(data)

# 3. Run the evaluation
print("Running AI Evaluation... This may take a moment.")
result = evaluate(
    dataset,
    metrics=[context_precision, faithfulness],
    llm=eval_llm,
    embeddings=eval_embeddings
)

# 4. Print the final spreadsheet metrics
# 4. Print the final spreadsheet metrics
df = result.to_pandas()
print("\n--- FINAL EVALUATION SCORES ---")
print(df)