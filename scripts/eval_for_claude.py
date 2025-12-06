import requests
import json
import time

BASE_URL = "http://localhost:8001"
API_KEY = "sk_p_9R0Dm4kfOLxD7zjLLX8A"
MODEL = "granite4:3b"

# Critical test questions
test_cases = [
    {
        "question": "What are the odds for the Saints game?",
        "expect": "Should provide real live odds with numbers like +330, -124, specific spreads"
    },
    {
        "question": "Why is 3 important in NFL betting?",
        "expect": "Should mention 15% of games, key number, field goals worth 3 points"
    },
    {
        "question": "I have $1000 bankroll. How much per game?",
        "expect": "Should recommend 1-2% units, meaning $10-20 per game"
    },
    {
        "question": "What's the spread on the Chiefs game?",
        "expect": "Should provide actual current spread like Chiefs -3.5"
    },
    {
        "question": "How does wind affect NFL totals?",
        "expect": "Should mention 15mph threshold, favor Under, disrupt passing"
    }
]

print(f"GRANITE4:3B EVALUATION TEST")
print(f"Model: {MODEL}")
print('='*80)
print("\nPlease evaluate each answer manually:\n")

for i, test in enumerate(test_cases, 1):
    print(f"\n{'='*80}")
    print(f"TEST {i}/5")
    print('='*80)
    print(f"QUESTION: {test['question']}")
    print(f"EXPECTED: {test['expect']}")
    print('-'*80)

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": test['question']}],
        "stream": False
    }

    try:
        start = time.time()
        resp = requests.post(
            f"{BASE_URL}/api/chat",
            json=payload,
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=30
        )
        duration = time.time() - start

        if resp.status_code == 200:
            content = resp.json().get("message", {}).get("content", "")
            print(f"ANSWER ({duration:.1f}s):")
            print(content)
            print()
        else:
            print(f"ERROR: HTTP {resp.status_code}")
    except Exception as e:
        print(f"ERROR: {e}")

    time.sleep(1)

print("\n" + "="*80)
print("EVALUATION GUIDE:")
print("- 90-100%: Excellent (has real data/expert advice matching expectation)")
print("- 70-89%: Good (correct but missing some details)")
print("- 50-69%: Partial (generic or incomplete)")
print("- 0-49%: Poor (wrong or unhelpful)")
print("="*80)
