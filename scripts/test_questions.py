import requests
import json
import sys
import time

BASE_URL = "http://localhost:8001"
# Using the key we created earlier
API_KEY = "sk_p_9R0Dm4kfOLxD7zjLLX8A"

def ask_question(question):
    print(f"\n--- QUESTION: '{question}' ---")

    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {
        "model": "llama3.2:latest",
        "messages": [{"role": "user", "content": question}],
        "stream": False
    }

    try:
        start = time.time()
        resp = requests.post(f"{BASE_URL}/api/chat", json=payload, headers=headers)
        duration = time.time() - start

        if resp.status_code == 200:
            content = resp.json().get("message", {}).get("content", "")
            print(f"ANSWER ({duration:.1f}s):\n{content}")
        else:
            print(f"Error: {resp.text}")

    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    questions = [
        "What is the Kelly Criterion?",
        "Why is the number 3 important in NFL betting?",
        "What are the live odds for NFL games right now?"
    ]

    for q in questions:
        ask_question(q)
