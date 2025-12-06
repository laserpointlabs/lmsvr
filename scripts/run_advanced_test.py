import requests
import json
import time
from advanced_test_questions import ALL_ADVANCED_QUESTIONS, PRIZEPICKS_ADVANCED

BASE_URL = "http://localhost:8001"
API_KEY = "sk_p_9R0Dm4kfOLxD7zjLLX8A"
MODEL = "granite4:3b"

def run_test(category, questions):
    print(f"\n{'='*80}")
    print(f"TESTING CATEGORY: {category}")
    print('='*80)

    for i, q in enumerate(questions, 1):
        print(f"\n[{i}] Q: {q}")

        payload = {
            "model": MODEL,
            "messages": [{"role": "user", "content": q}],
            "stream": False
        }

        try:
            start = time.time()
            resp = requests.post(
                f"{BASE_URL}/api/chat",
                json=payload,
                headers={"Authorization": f"Bearer {API_KEY}"},
                timeout=60
            )
            duration = time.time() - start

            if resp.status_code == 200:
                content = resp.json().get("message", {}).get("content", "")
                print(f"  ✓ ({duration:.1f}s) Answer snippet:")
                print(f"  {content[:300].replace(chr(10), ' ')}...")
            else:
                print(f"  ❌ HTTP {resp.status_code}")

        except Exception as e:
            print(f"  ❌ Error: {e}")

        time.sleep(1)

if __name__ == "__main__":
    print("RUNNING ADVANCED GAMBLER TEST")

    # Focus on PrizePicks and Sharp betting first
    run_test("PRIZEPICKS & PROPS", PRIZEPICKS_ADVANCED)

    # Run a sample of others
    sample_sharp = [ALL_ADVANCED_QUESTIONS[0], ALL_ADVANCED_QUESTIONS[4]]
    run_test("SHARP BETTING", sample_sharp)
