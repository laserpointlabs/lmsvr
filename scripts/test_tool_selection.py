import requests
import json

BASE_URL = "http://localhost:8001"
API_KEY = "sk_p_9R0Dm4kfOLxD7zjLLX8A"
MODEL = "qwen2.5:32b"

# Critical test - these should NOT call get_odds()
conceptual_questions = [
    ("Why is 3 important in NFL betting?", "search_guides"),
    ("I have $1000 bankroll. How much per game?", "search_guides"),
    ("How does wind affect NFL totals?", "search_guides"),
]

# These SHOULD call get_odds()
specific_questions = [
    ("What are the odds for the Saints game?", "get_odds"),
    ("What's the spread on the Chiefs game?", "get_odds"),
]

print(f"QWEN2.5:32B TOOL SELECTION TEST\n")

for question, expected_tool in conceptual_questions + specific_questions:
    print(f"Q: {question}")
    print(f"Expected: {expected_tool}")

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": question}],
        "stream": False
    }

    resp = requests.post(
        f"{BASE_URL}/api/chat",
        json=payload,
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=60
    )

    if resp.status_code == 200:
        content = resp.json().get("message", {}).get("content", "")

        # Check which tool was likely used based on response content
        has_live_data = "DraftKings" in content or "FanDuel" in content or "-110" in content
        has_guide_data = "Kelly" in content or "15%" in content or "key number" in content or "Unit" in content

        if has_live_data and expected_tool == "get_odds":
            print(f"  ✓ CORRECT TOOL\n")
        elif has_guide_data and expected_tool == "search_guides":
            print(f"  ✓ CORRECT TOOL\n")
        elif has_live_data and expected_tool == "search_guides":
            print(f"  ❌ WRONG TOOL - Used get_odds() when should use search_guides()\n")
        else:
            print(f"  ⚠ UNCLEAR\n")
    else:
        print(f"  ❌ HTTP {resp.status_code}\n")
