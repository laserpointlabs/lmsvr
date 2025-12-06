import requests
import json
import sys
import time
from test_questions_comprehensive import ALL_QUESTIONS, TRADITIONAL_SPORTSBOOK_QUESTIONS, STRATEGY_QUESTIONS, DFS_PRIZEPICKS_QUESTIONS, CONTEXTUAL_QUESTIONS, MULTI_PART_QUESTIONS

BASE_URL = "http://localhost:8001"
API_KEY = "sk_p_9R0Dm4kfOLxD7zjLLX8A"
MODEL = "llama3.2:latest"

def test_question(question, index, total):
    print(f"\n{'='*80}")
    print(f"Question {index}/{total}: {question}")
    print('='*80)

    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": question}],
        "stream": False
    }

    try:
        start = time.time()
        resp = requests.post(f"{BASE_URL}/api/chat", json=payload, headers=headers)
        duration = time.time() - start

        if resp.status_code == 200:
            content = resp.json().get("message", {}).get("content", "")

            # Analyze response
            has_real_data = "[REAL-TIME DATA" in content or any(str(x) in content for x in ['-110', '+150', '-120', 'DraftKings', 'FanDuel'])
            has_context_data = "Kelly Criterion" in content or "key number" in content or "Unit" in content
            is_error = "Error" in content or "I don't have" in content or "I apologize" in content

            print(f"\n✓ Response ({duration:.1f}s):")
            print(content[:500] + ("..." if len(content) > 500 else ""))

            print(f"\nAnalysis:")
            print(f"  - Used Live Data: {'YES' if has_real_data else 'NO'}")
            print(f"  - Used Betting Context: {'YES' if has_context_data else 'NO'}")
            print(f"  - Error/Limitation: {'YES' if is_error else 'NO'}")

            return {
                "question": question,
                "duration": duration,
                "has_real_data": has_real_data,
                "has_context_data": has_context_data,
                "is_error": is_error,
                "response_length": len(content)
            }
        else:
            print(f"✗ HTTP Error {resp.status_code}: {resp.text[:200]}")
            return {"question": question, "error": resp.status_code}

    except Exception as e:
        print(f"✗ Exception: {e}")
        return {"question": question, "error": str(e)}

def run_test_suite(questions, category_name, max_questions=None):
    print(f"\n\n{'#'*80}")
    print(f"# Testing Category: {category_name}")
    print(f"{'#'*80}")

    if max_questions:
        questions = questions[:max_questions]

    results = []
    for i, q in enumerate(questions, 1):
        result = test_question(q, i, len(questions))
        results.append(result)
        time.sleep(1)  # Rate limiting

    return results

def print_summary(all_results):
    print(f"\n\n{'='*80}")
    print("SUMMARY")
    print('='*80)

    total = len(all_results)
    with_live_data = sum(1 for r in all_results if r.get('has_real_data'))
    with_context = sum(1 for r in all_results if r.get('has_context_data'))
    errors = sum(1 for r in all_results if r.get('is_error'))

    print(f"Total Questions: {total}")
    print(f"Used Live Data: {with_live_data} ({with_live_data/total*100:.1f}%)")
    print(f"Used Betting Context: {with_context} ({with_context/total*100:.1f}%)")
    print(f"Errors/Limitations: {errors} ({errors/total*100:.1f}%)")

    avg_duration = sum(r.get('duration', 0) for r in all_results) / total if total > 0 else 0
    print(f"Average Response Time: {avg_duration:.1f}s")

if __name__ == "__main__":
    # Test a subset of each category
    all_results = []

    all_results += run_test_suite(TRADITIONAL_SPORTSBOOK_QUESTIONS, "Traditional Sportsbook (Live Odds)", max_questions=5)
    all_results += run_test_suite(STRATEGY_QUESTIONS, "Strategy & Bankroll", max_questions=5)
    all_results += run_test_suite(CONTEXTUAL_QUESTIONS, "Contextual/Glossary", max_questions=3)
    all_results += run_test_suite(MULTI_PART_QUESTIONS, "Multi-Part Analysis", max_questions=2)

    print_summary(all_results)
