import requests
import json
import time

BASE_URL = "http://localhost:8001"
API_KEY = "sk_p_9R0Dm4kfOLxD7zjLLX8A"
MODEL = "granite4:3b"

# Quick test with key questions
test_questions = [
    "What are the odds for the Saints game?",
    "Why is 3 such an important number in NFL betting?",
    "What's the spread on the Chiefs game?",
    "What is the Kelly Criterion?",
    "Who is favored in the Bills game?",
    "I have a $1000 bankroll. How much should I bet per game?"
]

print(f"Quick Test - Model: {MODEL}")
print('='*80)

successes = 0
failures = 0
times = []

for q in test_questions:
    print(f"\nQ: {q}")

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
            timeout=45
        )
        duration = time.time() - start
        times.append(duration)

        if resp.status_code == 200:
            content = resp.json().get("message", {}).get("content", "")

            # Check quality
            is_tool_call = '{"name"' in content[:100] or '<tool_call>' in content[:100] or '{"arguments"' in content[:100]
            has_data = any(kw in content for kw in ['Saints', 'Bills', 'Chiefs', '-110', 'Kelly', '15%', 'key number', '1%', '2%'])

            if is_tool_call:
                print(f"  ❌ TOOL LEAK ({duration:.1f}s): {content[:80]}...")
                failures += 1
            elif has_data:
                print(f"  ✓ SUCCESS ({duration:.1f}s): {content[:120]}...")
                successes += 1
            else:
                print(f"  ⚠ GENERIC ({duration:.1f}s): {content[:120]}...")
                failures += 1
        else:
            print(f"  ❌ HTTP {resp.status_code}")
            failures += 1

    except requests.Timeout:
        print(f"  ❌ TIMEOUT (45s)")
        failures += 1
    except Exception as e:
        print(f"  ❌ Exception: {e}")
        failures += 1

    time.sleep(0.5)

print(f"\n{'='*80}")
print(f"GRANITE4:3B RESULTS")
print('='*80)
print(f"✓ Successes: {successes}/6 ({successes/6*100:.0f}%)")
print(f"❌ Failures: {failures}/6 ({failures/6*100:.0f}%)")
if times:
    print(f"⚡ Avg Time: {sum(times)/len(times):.1f}s")
