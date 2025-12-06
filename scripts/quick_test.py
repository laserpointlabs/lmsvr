import requests
import json

BASE_URL = "http://localhost:8001"
API_KEY = "sk_p_9R0Dm4kfOLxD7zjLLX8A"

questions = [
    "What are the odds for the Saints game?",
    "Who is favored in the Bills game?",
    "What's the spread on the Chiefs game?",
]

for q in questions:
    print(f"\nQ: {q}")
    resp = requests.post(f"{BASE_URL}/api/chat",
        json={"model": "llama3.2:latest", "messages": [{"role": "user", "content": q}], "stream": False},
        headers={"Authorization": f"Bearer {API_KEY}"})

    if resp.status_code == 200:
        content = resp.json().get("message", {}).get("content", "")
        # Check if it's a tool call or actual answer
        if '{"name"' in content or '"parameters"' in content:
            print(f"❌ RAW TOOL CALL: {content[:100]}")
        elif "Saints" in content or "Bills" in content or "Chiefs" in content or any(str(x) in content for x in ['-110', '+150', '-3.5']):
            print(f"✓ SUCCESS: {content[:200]}...")
        else:
            print(f"⚠ UNCLEAR: {content[:200]}...")
    else:
        print(f"❌ Error: {resp.status_code}")
