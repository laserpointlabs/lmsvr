import requests
import json

BASE_URL = "http://localhost:8001"
API_KEY = "sk_p_9R0Dm4kfOLxD7zjLLX8A"
MODEL = "qwen2.5:32b"

# Test the questions that were failing
failing_questions = [
    ("Why is 3 such an important number in NFL betting?", "Should mention 15% of games, key number, field goals"),
    ("How does wind affect NFL totals?", "Should mention 15mph threshold, favor Under"),
    ("What's a lookahead spot in NFL betting?", "Should mention looking past current opponent"),
    ("I have a $1000 bankroll. How much should I bet per game?", "Should mention 1-2% unit sizing")
]

print(f"Testing Improved System with {MODEL}\n")

for question, expected in failing_questions:
    print(f"{'='*80}")
    print(f"Q: {question}")
    print(f"Expected: {expected}")
    print('='*80)

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": question}],
        "stream": False
    }

    try:
        resp = requests.post(
            f"{BASE_URL}/api/chat",
            json=payload,
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=60
        )

        if resp.status_code == 200:
            content = resp.json().get("message", {}).get("content", "")

            # Check if expected content is present
            keywords = expected.lower().replace("should mention ", "").split(", ")
            found_keywords = [kw for kw in keywords if any(word in content.lower() for word in kw.split())]

            if len(found_keywords) >= len(keywords) / 2:
                print(f"✓ EXCELLENT - Found {len(found_keywords)}/{len(keywords)} key concepts")
            elif found_keywords:
                print(f"⚠ PARTIAL - Found {len(found_keywords)}/{len(keywords)} key concepts")
            else:
                print(f"❌ POOR - Missing expected content")

            print(f"\nAnswer: {content[:400]}...\n")
        else:
            print(f"❌ Error {resp.status_code}\n")

    except Exception as e:
        print(f"❌ Exception: {e}\n")
