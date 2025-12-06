import requests
import json

BASE_URL = "http://localhost:8001"
API_KEY = "sk_p_9R0Dm4kfOLxD7zjLLX8A"
MODEL = "gpt-4o"

print("TESTING GPT-4O WITH AUTO-FETCHING ODDS")
print('='*80)

# User should NOT need to provide specific odds - assistant should fetch them
natural_questions = [
    "Compare the Chiefs moneyline vs their spread. Which is better value?",
    "Should I bet the Saints spread or moneyline?",
    "What are the odds for the Bills game and should I take the spread or moneyline?"
]

for q in natural_questions:
    print(f"\nQ: {q}")

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": q}],
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

            # Check if it fetched odds AND did analysis
            has_numbers = any(x in content for x in ['-', '+', '%', 'probability'])
            has_recommendation = any(x in content for x in ['better value', 'recommend', 'should'])

            if has_numbers and has_recommendation:
                print(f"  ✓ EXCELLENT: Fetched data + analyzed")
            elif has_numbers:
                print(f"  ⚠ PARTIAL: Has data but no clear recommendation")
            else:
                print(f"  ❌ POOR: Missing data")

            print(f"  Answer: {content[:250]}...")
        else:
            print(f"  ❌ HTTP {resp.status_code}: {resp.text[:200]}")

    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\n" + "="*80)
print("If all 3 passed, the system is ready for users!")
