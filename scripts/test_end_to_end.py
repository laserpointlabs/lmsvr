import requests
import json
import sys

BASE_URL = "http://localhost:8001"
API_KEY = "sk_p_9R0Dm4kfOLxD7zjLLX8A" # From previous step

def run_test():
    # 1. Register Device
    print("1. Registering Device...")
    resp = requests.post(f"{BASE_URL}/api/register-device", json={
        "api_key": API_KEY,
        "device_name": "TestScript"
    })
    if resp.status_code != 200:
        print(f"Registration failed: {resp.text}")
        return

    token = resp.json()["device_token"]
    print(f"Got token: {token}")

    # 2. Verify Device (Auth check)
    print("\n2. Verifying Device...")
    resp = requests.post(f"{BASE_URL}/api/verify-device", json={"device_token": token})
    print(f"Status: {resp.json()['valid']}")

    # 3. Test Chat with Tool (Live Sports)
    print("\n3. Testing Chat (Tools: Live Sports)...")
    # Note: Auth middleware requires Bearer token with API KEY, not device token for this endpoint
    # Based on auth.py: credentials.credentials -> verify_api_key -> key_hash
    # So we should pass the raw API key as a Bearer token.

    chat_headers = {"Authorization": f"Bearer {API_KEY}"}

    payload = {
        "model": "llama3.2:latest",
        "messages": [{"role": "user", "content": "What are the live odds for the Chiefs game?"}],
        "stream": False
    }

    try:
        resp = requests.post(f"{BASE_URL}/api/chat", json=payload, headers=chat_headers)
        print(f"Response Code: {resp.status_code}")
        response_json = resp.json()
        content = response_json.get("message", {}).get("content", "")
        print(f"Content: {content}")

        if "Kansas City" in content or "1.75" in content:
             print("SUCCESS: Tool data found in response!")
        else:
             print("WARNING: Tool data might be missing.")

    except Exception as e:
        print(f"Chat failed: {e}")

    # 4. Test Chat with Tool (Betting Context)
    print("\n4. Testing Chat (Tools: Betting Context)...")
    payload["messages"] = [{"role": "user", "content": "Explain what a moneyline is based on the betting guides."}]

    try:
        resp = requests.post(f"{BASE_URL}/api/chat", json=payload, headers=chat_headers)
        content = resp.json().get("message", {}).get("content", "")
        print(f"Content: {content}")

        if "simplest bet" in content:
             print("SUCCESS: Context data found in response!")

    except Exception as e:
        print(f"Chat failed: {e}")

if __name__ == "__main__":
    run_test()
