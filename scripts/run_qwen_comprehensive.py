import requests
import json
import time
from test_questions_comprehensive import ALL_QUESTIONS, TRADITIONAL_SPORTSBOOK_QUESTIONS, STRATEGY_QUESTIONS, DFS_PRIZEPICKS_QUESTIONS, CONTEXTUAL_QUESTIONS, MULTI_PART_QUESTIONS

BASE_URL = "http://localhost:8001"
API_KEY = "sk_p_9R0Dm4kfOLxD7zjLLX8A"
MODEL = "qwen2.5:32b"

def test_question(question, index, total):
    print(f"\n{'='*80}")
    print(f"[{index}/{total}] {question}")
    print('='*80)

    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": question}],
        "stream": False
    }

    try:
        start = time.time()
        resp = requests.post(f"{BASE_URL}/api/chat", json=payload, headers=headers, timeout=60)
        duration = time.time() - start

        if resp.status_code == 200:
            content = resp.json().get("message", {}).get("content", "")

            # Analyze response
            has_real_data = any(keyword in content for keyword in ['-110', '+150', '-120', 'DraftKings', 'FanDuel', 'BetUS'])
            has_context_data = any(keyword in content for keyword in ['Kelly Criterion', 'key number', 'Unit', 'bankroll', 'flat betting', 'Variable', 'lookahead'])
            is_tool_call = '{"name"' in content[:100] or '<tool_call>' in content[:100]
            is_error = "don't have" in content or "I apologize" in content or "I'm sorry" in content

            # Quality score
            if is_tool_call:
                status = "❌ TOOL LEAK"
            elif has_real_data or has_context_data:
                status = "✓ GOOD"
            elif is_error:
                status = "⚠ ERROR"
            else:
                status = "⚠ GENERIC"

            print(f"{status} ({duration:.1f}s)")
            print(f"Response: {content[:300]}...")

            return {
                "question": question,
                "status": status,
                "duration": duration,
                "has_real_data": has_real_data,
                "has_context_data": has_context_data,
                "response_length": len(content)
            }
        else:
            print(f"❌ HTTP {resp.status_code}")
            return {"question": question, "error": resp.status_code}

    except requests.Timeout:
        print(f"❌ TIMEOUT (60s)")
        return {"question": question, "error": "timeout"}
    except Exception as e:
        print(f"❌ Exception: {e}")
        return {"question": question, "error": str(e)}

if __name__ == "__main__":
    print(f"{'#'*80}")
    print(f"# COMPREHENSIVE TEST SUITE - Model: {MODEL}")
    print(f"{'#'*80}\n")

    categories = [
        ("Live Odds", TRADITIONAL_SPORTSBOOK_QUESTIONS[:8]),
        ("Strategy", STRATEGY_QUESTIONS[:6]),
        ("Contextual", CONTEXTUAL_QUESTIONS[:4]),
        ("Multi-Part", MULTI_PART_QUESTIONS[:2])
    ]

    all_results = []

    for cat_name, questions in categories:
        print(f"\n{'#'*80}")
        print(f"# {cat_name}")
        print(f"{'#'*80}")

        for i, q in enumerate(questions, 1):
            result = test_question(q, i, len(questions))
            all_results.append(result)
            time.sleep(1)  # Rate limiting between questions

    # Summary
    print(f"\n\n{'='*80}")
    print("FINAL SUMMARY")
    print('='*80)

    total = len(all_results)
    good = sum(1 for r in all_results if r.get('status', '').startswith('✓'))
    tool_leaks = sum(1 for r in all_results if 'TOOL LEAK' in r.get('status', ''))
    errors = sum(1 for r in all_results if 'ERROR' in r.get('status', ''))
    with_live = sum(1 for r in all_results if r.get('has_real_data'))
    with_context = sum(1 for r in all_results if r.get('has_context_data'))

    print(f"Model: {MODEL}")
    print(f"Total Questions: {total}")
    print(f"✓ Good Answers: {good}/{total} ({good/total*100:.1f}%)")
    print(f"❌ Tool Call Leaks: {tool_leaks}/{total} ({tool_leaks/total*100:.1f}%)")
    print(f"⚠ Errors: {errors}/{total} ({errors/total*100:.1f}%)")
    print(f"\nData Sources:")
    print(f"  - Used Live API: {with_live}/{total} ({with_live/total*100:.1f}%)")
    print(f"  - Used Guides: {with_context}/{total} ({with_context/total*100:.1f}%)")

    avg_time = sum(r.get('duration', 0) for r in all_results if 'duration' in r) / len([r for r in all_results if 'duration' in r])
    print(f"\nAvg Response Time: {avg_time:.1f}s")
