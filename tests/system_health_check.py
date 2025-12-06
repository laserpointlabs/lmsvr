import requests
import json
import os
import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")
API_KEY = os.getenv("SYSTEM_TEST_KEY") # We might need to generate a key or use a known one
LOG_FILE = Path("logs/system_health.log")
LOG_FILE.parent.mkdir(exist_ok=True)

# We need a valid customer API key to run tests against the API Gateway
# If not provided in env, try to grab one from the database or warn user
if not API_KEY:
    # Fallback to a placeholder, or try to read from a local file if we were running locally
    # For this script to work in CI, we'd need to mock authentication or provide a key secret
    print("WARNING: SYSTEM_TEST_KEY not set. Attempting to use a hardcoded key or fail.")
    # In a real scenario, we might generate a temp key
    pass

def log_result(test_name, question, answer, status="PASS"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [{status}] {test_name}\nQ: {question}\nA: {answer}\n" + "-"*50 + "\n"

    print(entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)

def run_test_query(test_name, question, model="gpt-4o"):
    print(f"Running test: {test_name}...")

    # If we don't have a key, we can't hit the API gateway authenticated endpoints easily
    # unless we bypass auth or generate one.
    # Assuming we have a key for now.

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": question}],
        "stream": False
    }

    try:
        response = requests.post(f"{API_BASE_URL}/api/chat", headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            answer = data.get("message", {}).get("content", "No content received")
            log_result(test_name, question, answer, "PASS")
            return True
        else:
            log_result(test_name, question, f"Error: {response.status_code} - {response.text}", "FAIL")
            return False
    except Exception as e:
        log_result(test_name, question, f"Exception: {str(e)}", "FAIL")
        return False

def run_suite():
    # Ensure we have a key. For local dev, we can try to grep one or ask user to set it.
    # For now, I'll assume the user has set SYSTEM_TEST_KEY in .env
    global API_KEY
    if not API_KEY:
        # Try to find a key from the CLI output or database if running locally?
        # Let's just warn.
        print("Error: SYSTEM_TEST_KEY not found in .env. Please add a valid API Key to run tests.")
        return

    tests = [
        {
            "name": "NBA Analysis",
            "question": "What's the outlook for the Lakers game? Any injuries?"
        },
        {
            "name": "NCAAF Strategy",
            "question": "Find me a good Wong Teaser opportunity for college football this weekend."
        },
        {
            "name": "NFL Weather",
            "question": "Is the weather going to be a factor in the Bills game? Should I bet the Under?"
        },
        {
            "name": "MLB Line Movement",
            "question": "Check for any sharp money or steam moves in MLB today."
        },
        {
            "name": "NCAAB Value",
            "question": "Scan college basketball for any big underdogs or key number value."
        },
        {
            "name": "Alert Analysis Demo",
            "question": "Analyze this line movement: Washington Commanders @ Minnesota Vikings - Spread moved +4.0 pts. Why is this happening? Check news and injuries."
        }
    ]

    print(f"Starting Test Suite at {datetime.datetime.now()}")
    success_count = 0

    for test in tests:
        if run_test_query(test["name"], test["question"]):
            success_count += 1

    print(f"Test Suite Complete. {success_count}/{len(tests)} passed.")
    print(f"Results logged to {LOG_FILE.absolute()}")

if __name__ == "__main__":
    run_suite()
