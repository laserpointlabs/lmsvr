import requests
import json

BASE_URL = "http://localhost:8001"
API_KEY = "sk_p_9R0Dm4kfOLxD7zjLLX8A"
MODEL = "granite4:3b"

# The specific failing question
question = "Compare the implied probability of the Chiefs -200 moneyline vs their -3.5 spread at -110."

print(f"Testing Analysis Capability - Model: {MODEL}")
print('='*80)
print(f"Q: {question}\n")

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
    print(f"Answer:\n{content}")

    # Check if it actually calculated probability
    if "%" in content or "percent" in content:
        print("\n✓ SUCCESS: Probability calculation found.")
    else:
        print("\n❌ FAILURE: No probability calculation found.")
else:
    print(f"Error: {resp.status_code}")
