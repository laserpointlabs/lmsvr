import requests
import json
import time
from test_questions_comprehensive import ALL_QUESTIONS, TRADITIONAL_SPORTSBOOK_QUESTIONS, STRATEGY_QUESTIONS, DFS_PRIZEPICKS_QUESTIONS, CONTEXTUAL_QUESTIONS, MULTI_PART_QUESTIONS

BASE_URL = "http://localhost:8001"
API_KEY = "sk_p_9R0Dm4kfOLxD7zjLLX8A"
MODEL = "granite3.2:8b"  # Testing the winning model

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
        resp = requests.post(f"{BASE_URL}/api/chat", json=payload, headers=headers, timeout=30)
        duration = time.time() - start
        
        if resp.status_code == 200:
            content = resp.json().get("message", {}).get("content", "")
            
            # Analyze response
            has_real_data = any(keyword in content for keyword in ['-110', '+150', '-120', 'DraftKings', 'FanDuel', 'BetUS'])
            has_context_data = any(keyword in content for keyword in ['Kelly Criterion', 'key number', 'Unit', 'bankroll', 'flat betting'])
            is_tool_call = '{"name"' in content[:100] or '<tool_call>' in content[:100]
            is_error = "Error" in content or "I don't have" in content[:200] or "I apologize" in content[:200]
            
            status = "✓ GOOD" if (has_real_data or has_context_data) and not is_tool_call else ("❌ TOOL CALL" if is_tool_call else "⚠ CHECK")
            
            print(f"\n{status} Response ({duration:.1f}s):")
            print(content[:400] + ("..." if len(content) > 400 else ""))
            
            print(f"\nAnalysis:")
            print(f"  - Live Data: {'YES' if has_real_data else 'NO'}")
            print(f"  - Context: {'YES' if has_context_data else 'NO'}")
            print(f"  - Tool Call Leak: {'YES' if is_tool_call else 'NO'}")
            print(f"  - Error: {'YES' if is_error else 'NO'}")
            
            return {
                "question": question,
                "duration": duration,
                "has_real_data": has_real_data,
                "has_context_data": has_context_data,
                "is_tool_call": is_tool_call,
                "is_error": is_error,
                "status": status
            }
        else:
            print(f"✗ HTTP Error {resp.status_code}: {resp.text[:200]}")
            return {"question": question, "error": resp.status_code, "status": "❌ ERROR"}
            
    except Exception as e:
        print(f"✗ Exception: {e}")
        return {"question": question, "error": str(e), "status": "❌ ERROR"}

def run_test_suite(questions, category_name, max_questions=None):
    print(f"\n\n{'#'*80}")
    print(f"# {category_name}")
    print(f"{'#'*80}")
    
    if max_questions:
        questions = questions[:max_questions]
    
    results = []
    for i, q in enumerate(questions, 1):
        result = test_question(q, i, len(questions))
        results.append(result)
        time.sleep(0.5)  # Rate limiting
    
    return results

def print_summary(all_results):
    print(f"\n\n{'='*80}")
    print(f"SUMMARY - Model: {MODEL}")
    print('='*80)
    
    total = len(all_results)
    good = sum(1 for r in all_results if r.get('status', '').startswith('✓'))
    tool_leaks = sum(1 for r in all_results if r.get('is_tool_call'))
    with_live_data = sum(1 for r in all_results if r.get('has_real_data'))
    with_context = sum(1 for r in all_results if r.get('has_context_data'))
    errors = sum(1 for r in all_results if r.get('is_error'))
    
    print(f"Total Questions: {total}")
    print(f"Good Answers: {good} ({good/total*100:.1f}%)")
    print(f"Used Live Data: {with_live_data} ({with_live_data/total*100:.1f}%)")
    print(f"Used Context: {with_context} ({with_context/total*100:.1f}%)")
    print(f"Tool Call Leaks: {tool_leaks} ({tool_leaks/total*100:.1f}%)")
    print(f"Errors: {errors} ({errors/total*100:.1f}%)")
    
    avg_duration = sum(r.get('duration', 0) for r in all_results if 'duration' in r) / total if total > 0 else 0
    print(f"Average Response Time: {avg_duration:.1f}s")

if __name__ == "__main__":
    # Test a subset of each category with granite
    all_results = []
    
    all_results += run_test_suite(TRADITIONAL_SPORTSBOOK_QUESTIONS, "Traditional Sportsbook (Live Odds)", max_questions=5)
    all_results += run_test_suite(STRATEGY_QUESTIONS, "Strategy & Bankroll", max_questions=5)
    all_results += run_test_suite(CONTEXTUAL_QUESTIONS, "Contextual/Glossary", max_questions=3)
    all_results += run_test_suite(MULTI_PART_QUESTIONS, "Multi-Part Analysis", max_questions=2)
    
    print_summary(all_results)

