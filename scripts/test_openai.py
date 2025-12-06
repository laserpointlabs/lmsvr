import requests
import json
import time

BASE_URL = "http://localhost:8001"
API_KEY = "sk_p_9R0Dm4kfOLxD7zjLLX8A"
MODEL = "gpt-4o"

print(f"TESTING OPENAI INTEGRATION ({MODEL})")
print('='*80)

question = "Compare the implied probability of the Chiefs -200 moneyline vs their -3.5 spread at -110."
print(f"Q: {question}\n")

payload = {
    "model": MODEL,
    "messages": [{"role": "user", "content": question}],
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
        print(f"✓ SUCCESS ({duration:.1f}s):")
        print(content)

        if "66" in content and "52" in content:
            print("\n[Analysis verified: Correct math detected]")
        else:
            print("\n[Analysis check: Check output for correctness]")

    elif resp.status_code == 500:
        print(f"❌ FAILED: {resp.text}")
        if "OPENAI_API_KEY not configured" in resp.text:
            print(">> The API key was not loaded properly. Check .env and restart.")
    else:
        print(f"❌ ERROR {resp.status_code}: {resp.text}")

except Exception as e:
    print(f"❌ Exception: {e}")
