import requests
import json
import time
from test_questions_comprehensive import TRADITIONAL_SPORTSBOOK_QUESTIONS, STRATEGY_QUESTIONS, CONTEXTUAL_QUESTIONS, MULTI_PART_QUESTIONS

BASE_URL = "http://localhost:8001"
API_KEY = "sk_p_9R0Dm4kfOLxD7zjLLX8A"
TEST_MODEL = "granite4:3b"
EVALUATOR_MODEL = "granite4:3b"  # Use same model to evaluate itself

def ask_question(question):
    """Ask the betting assistant a question."""
    payload = {
        "model": TEST_MODEL,
        "messages": [{"role": "user", "content": question}],
        "stream": False
    }

    try:
        resp = requests.post(
            f"{BASE_URL}/api/chat",
            json=payload,
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=45
        )

        if resp.status_code == 200:
            return resp.json().get("message", {}).get("content", "")
        else:
            return f"ERROR: HTTP {resp.status_code}"
    except Exception as e:
        return f"ERROR: {str(e)}"

def evaluate_answer(question, answer):
    """Use an LLM to evaluate the quality and correctness of an answer."""

    evaluation_prompt = f"""You are evaluating a sports betting assistant's answer for quality and correctness.

QUESTION: {question}

ANSWER: {answer}

Evaluate this answer on the following criteria:
1. **Accuracy**: Does it provide factual, correct information? (avoid hallucinations)
2. **Relevance**: Does it directly answer the question asked?
3. **Data Source**: Does it cite real odds/data or expert guides when appropriate?
4. **Completeness**: Is the answer thorough and useful?

Rate the answer on a 0-100 confidence scale:
- 90-100: Excellent answer with real data/expert advice
- 70-89: Good answer, mostly correct
- 50-69: Partial answer or generic advice
- 0-49: Poor, incorrect, or off-topic

Respond ONLY with a JSON object:
{{"confidence": <0-100>, "reason": "<one sentence explanation>"}}"""

    payload = {
        "model": EVALUATOR_MODEL,
        "messages": [{"role": "user", "content": evaluation_prompt}],
        "stream": False
    }

    try:
        resp = requests.post(
            f"{BASE_URL}/api/chat",
            json=payload,
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=30
        )

        if resp.status_code == 200:
            eval_text = resp.json().get("message", {}).get("content", "")

            # Try to parse JSON from response
            # The LLM might wrap it in markdown code blocks
            eval_text = eval_text.strip()
            if '```json' in eval_text:
                eval_text = eval_text.split('```json')[1].split('```')[0].strip()
            elif '```' in eval_text:
                eval_text = eval_text.split('```')[1].split('```')[0].strip()

            try:
                result = json.loads(eval_text)
                return result.get('confidence', 0), result.get('reason', 'No reason provided')
            except json.JSONDecodeError:
                # Try to extract confidence number from text
                if 'confidence' in eval_text.lower():
                    import re
                    match = re.search(r'"?confidence"?\s*:?\s*(\d+)', eval_text)
                    if match:
                        return int(match.group(1)), eval_text[:100]
                return 0, "Failed to parse evaluation"
        else:
            return 0, f"Evaluation failed: HTTP {resp.status_code}"
    except Exception as e:
        return 0, f"Evaluation error: {str(e)}"

def run_test_suite(questions, category_name, max_questions=None):
    print(f"\n{'#'*80}")
    print(f"# {category_name}")
    print(f"{'#'*80}\n")

    if max_questions:
        questions = questions[:max_questions]

    results = []

    for i, q in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] {q}")

        # Get answer
        start = time.time()
        answer = ask_question(q)
        duration = time.time() - start

        # Evaluate answer
        confidence, reason = evaluate_answer(q, answer)

        # Determine status
        if confidence >= 80:
            status = "✓ GOOD"
        elif confidence >= 50:
            status = "⚠ OK"
        else:
            status = "❌ POOR"

        print(f"  {status} | Confidence: {confidence}% | Time: {duration:.1f}s")
        print(f"  Reason: {reason}")
        print(f"  Answer: {answer[:150]}...")
        print()

        results.append({
            "question": q,
            "confidence": confidence,
            "duration": duration,
            "status": status,
            "answer_length": len(answer)
        })

        time.sleep(1)  # Rate limiting

    return results

if __name__ == "__main__":
    all_results = []

    all_results += run_test_suite(TRADITIONAL_SPORTSBOOK_QUESTIONS, "Live Odds", max_questions=6)
    all_results += run_test_suite(STRATEGY_QUESTIONS, "Strategy", max_questions=5)
    all_results += run_test_suite(MULTI_PART_QUESTIONS, "Multi-Part", max_questions=2)

    # Summary
    total = len(all_results)
    high_conf = sum(1 for r in all_results if r['confidence'] >= 80)
    avg_conf = sum(r['confidence'] for r in all_results) / total if total > 0 else 0
    avg_time = sum(r['duration'] for r in all_results) / total if total > 0 else 0

    print(f"{'='*80}")
    print(f"FINAL SUMMARY - {TEST_MODEL}")
    print('='*80)
    print(f"Total Questions: {total}")
    print(f"✓ High Confidence (≥80%): {high_conf}/{total} ({high_conf/total*100:.1f}%)")
    print(f"📊 Avg Confidence Score: {avg_conf:.1f}%")
    print(f"⚡ Avg Response Time: {avg_time:.1f}s")
