import requests
import json
import sys

BASE_URL = "http://localhost:8001"
# Using the key we created earlier
API_KEY = "sk_p_9R0Dm4kfOLxD7zjLLX8A"

def run_test():
    print("Testing Live Sports Data (Real API)...")

    headers = {"Authorization": f"Bearer {API_KEY}"}

    # Ask for NFL odds which should trigger get_odds("americanfootball_nfl")
    payload = {
        "model": "llama3.2:latest",
        "messages": [{"role": "user", "content": "What are the live odds for upcoming NFL games?"}],
        "stream": False
    }

    try:
        resp = requests.post(f"{BASE_URL}/api/chat", json=payload, headers=headers)
        print(f"Response Code: {resp.status_code}")

        if resp.status_code == 200:
            content = resp.json().get("message", {}).get("content", "")
            print(f"\nLLM Response:\n{content[:500]}...") # Print first 500 chars

            if "Bookmaker" in content or "Moneyline" in content or "+" in content or "-" in content:
                print("\nSUCCESS: Real odds data appears to be present.")
            else:
                print("\nWARNING: Response might not contain odds data. Check logs.")
        else:
            print(f"Error: {resp.text}")

    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    run_test()
