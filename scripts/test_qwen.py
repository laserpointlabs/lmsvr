import requests
import json
import time

BASE_URL = "http://localhost:8001"
API_KEY = "sk_p_9R0Dm4kfOLxD7zjLLX8A"

# Test qwen2.5:32b with longer timeout
MODEL = "qwen2.5:32b"

questions = [
    "What are the odds for the Saints game?",
    "What is the Kelly Criterion?",
    "Who is favored in the Bills game?",
    "What's the spread on the Chiefs game?"
]

print(f"Testing {MODEL} with extended timeout (60s)...")

for q in questions:
    print(f"\n{'='*80}")
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
            
            # Check quality
            is_tool_call = '{"name"' in content[:100] or '<tool_call>' in content[:100]
            has_data = any(kw in content for kw in ['Saints', 'Bills', 'Chiefs', '-110', 'Kelly', 'bankroll'])
            
            if is_tool_call:
                print(f"❌ TOOL CALL ({duration:.1f}s)")
            elif has_data:
                print(f"✓ SUCCESS ({duration:.1f}s): {content[:300]}...")
            else:
                print(f"⚠ UNCLEAR ({duration:.1f}s): {content[:300]}...")
        else:
            print(f"❌ Error {resp.status_code}")
    
    except requests.Timeout:
        print(f"❌ TIMEOUT (60s)")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    time.sleep(1)

