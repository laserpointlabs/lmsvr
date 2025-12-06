import requests
import json

BASE_URL = "http://localhost:8001"
API_KEY = "sk_p_9R0Dm4kfOLxD7zjLLX8A"
MODEL = "granite4:3b"

# Test critical questions with manual review
questions = [
    "What are the odds for the Saints game?",
    "Why is 3 important in NFL betting?",
    "How does wind affect NFL totals?",
    "I have $1000 bankroll. How much per game?",
    "What's the spread on the Chiefs game?"
]

print(f"GRANITE4:3B MANUAL REVIEW TEST\n")

for i, q in enumerate(questions, 1):
    print(f"{'='*80}")
    print(f"[{i}/5] {q}")
    print('='*80)

    resp = requests.post(
        f"{BASE_URL}/api/chat",
        json={"model": MODEL, "messages": [{"role": "user", "content": q}], "stream": False},
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=30
    )

    if resp.status_code == 200:
        content = resp.json().get("message", {}).get("content", "")
        print(content)
        print()
    else:
        print(f"ERROR: {resp.status_code}")
