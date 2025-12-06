import requests
import json
import time

BASE_URL = "http://localhost:8001"
API_KEY = "sk_p_9R0Dm4kfOLxD7zjLLX8A"
MODEL = "granite4:3b"

print("TESTING NEW NFL DATA MCP (Stats & Injuries)\n")

questions = [
    "Get the team stats for the Kansas City Chiefs.",
    "Are there any injuries for the Buffalo Bills?",
    "Give me a betting recommendation for the Chiefs game based on injuries and odds."
]

for q in questions:
    print(f"{'='*80}")
    print(f"Q: {q}")
    print('='*80)

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

            # Check if new tools were used
            has_espn_data = "ESPN" in content or "Record" in content or "INJURY NEWS" in content
            has_odds = "Odds API" in content or "-110" in content

            status = "✓ SUCCESS" if has_espn_data else "❌ FAILED"

            print(f"{status} ({duration:.1f}s)")
            print(f"Response snippet: {content[:300]}...")
        else:
            print(f"❌ HTTP {resp.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")
