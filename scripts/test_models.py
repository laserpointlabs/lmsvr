import requests
import json
import sys
import time

BASE_URL = "http://localhost:8001"
API_KEY = "sk_p_9R0Dm4kfOLxD7zjLLX8A"

def ask_question(question, model):
    print(f"\n--- MODEL: {model} ---")
    print(f"QUESTION: '{question}'")

    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": question}],
        "stream": False
    }

    try:
        start = time.time()
        resp = requests.post(f"{BASE_URL}/api/chat", json=payload, headers=headers)
        duration = time.time() - start

        if resp.status_code == 200:
            content = resp.json().get("message", {}).get("content", "")
            print(f"ANSWER ({duration:.1f}s):\n{content[:600]}...")
        else:
            print(f"Error: {resp.text}")

    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    # Test with different models
    question = "What are the odds for the Saints game?"

    models = ["qwen2.5-coder:32b", "mistral:latest", "llama3.2:latest"]

    for model in models:
        ask_question(question, model)
