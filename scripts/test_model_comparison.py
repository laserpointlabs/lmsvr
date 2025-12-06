import requests
import json
import time

BASE_URL = "http://localhost:8001"
API_KEY = "sk_p_9R0Dm4kfOLxD7zjLLX8A"

TEST_QUESTIONS = [
    "What are the odds for the Saints game?",
    "What is the Kelly Criterion?",
    "Who is favored in the Bills game?"
]

MODELS_TO_TEST = [
    "granite3.2:8b",
    "qwen2.5:32b",
    "llama3.2:latest"
]

def test_model(model_name):
    print(f"\n{'='*80}")
    print(f"Testing Model: {model_name}")
    print('='*80)
    
    results = {"model": model_name, "successes": 0, "failures": 0, "avg_time": 0}
    times = []
    
    for question in TEST_QUESTIONS:
        print(f"\nQ: {question}")
        
        headers = {"Authorization": f"Bearer {API_KEY}"}
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": question}],
            "stream": False
        }
        
        try:
            start = time.time()
            resp = requests.post(f"{BASE_URL}/api/chat", json=payload, headers=headers, timeout=30)
            duration = time.time() - start
            times.append(duration)
            
            if resp.status_code == 200:
                content = resp.json().get("message", {}).get("content", "")
                
                # Check if it's a proper answer or raw tool call
                is_tool_call = '{"name"' in content[:100] or '"parameters"' in content[:100]
                has_data = any(keyword in content for keyword in ['Saints', 'Bills', '-110', '+150', 'Kelly', 'bankroll'])
                
                if is_tool_call:
                    print(f"  ❌ RAW TOOL CALL: {content[:80]}...")
                    results["failures"] += 1
                elif has_data:
                    print(f"  ✓ SUCCESS ({duration:.1f}s): {content[:150]}...")
                    results["successes"] += 1
                else:
                    print(f"  ⚠ UNCLEAR ({duration:.1f}s): {content[:150]}...")
                    results["failures"] += 1
            else:
                print(f"  ❌ HTTP {resp.status_code}")
                results["failures"] += 1
                
        except Exception as e:
            print(f"  ❌ Exception: {e}")
            results["failures"] += 1
        
        time.sleep(0.5)  # Rate limiting
    
    results["avg_time"] = sum(times) / len(times) if times else 0
    return results

if __name__ == "__main__":
    all_results = []
    
    for model in MODELS_TO_TEST:
        result = test_model(model)
        all_results.append(result)
        time.sleep(1)
    
    print(f"\n\n{'='*80}")
    print("FINAL COMPARISON")
    print('='*80)
    for r in all_results:
        success_rate = r['successes'] / (r['successes'] + r['failures']) * 100 if (r['successes'] + r['failures']) > 0 else 0
        print(f"{r['model']:<20} | Success: {r['successes']}/3 ({success_rate:.0f}%) | Avg Time: {r['avg_time']:.1f}s")
    
    # Recommendation
    best = max(all_results, key=lambda x: (x['successes'], -x['avg_time']))
    print(f"\n✓ RECOMMENDED: {best['model']}")

