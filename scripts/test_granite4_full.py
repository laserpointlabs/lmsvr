import requests
import json
import time
from test_questions_comprehensive import TRADITIONAL_SPORTSBOOK_QUESTIONS, STRATEGY_QUESTIONS, CONTEXTUAL_QUESTIONS, MULTI_PART_QUESTIONS

BASE_URL = "http://localhost:8001"
API_KEY = "sk_p_9R0Dm4kfOLxD7zjLLX8A"
MODEL = "granite4:3b"

def test_batch(questions, category_name):
    print(f"\n{'#'*80}")
    print(f"# {category_name} - Model: {MODEL}")
    print(f"{'#'*80}\n")

    results = []
    for i, q in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] {q}")

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
                timeout=45
            )
            duration = time.time() - start

            if resp.status_code == 200:
                content = resp.json().get("message", {}).get("content", "")

                # Quality checks
                is_tool_leak = any(marker in content[:150] for marker in ['{"name"', '<tool_call>', '{"arguments"'])
                has_real_data = any(kw in content for kw in ['-110', '+150', 'DraftKings', 'FanDuel'])
                has_context = any(kw in content for kw in ['Kelly', 'bankroll', 'key number', '15%', 'Unit'])

                if is_tool_leak:
                    status = "❌ LEAK"
                elif has_real_data or has_context:
                    status = "✓"
                else:
                    status = "⚠"

                print(f"  {status} ({duration:.1f}s): {content[:150]}...")

                results.append({
                    "success": status == "✓",
                    "duration": duration,
                    "has_data": has_real_data or has_context
                })
            else:
                print(f"  ❌ HTTP {resp.status_code}")
                results.append({"success": False})

        except requests.Timeout:
            print(f"  ❌ TIMEOUT")
            results.append({"success": False})
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results.append({"success": False})

        time.sleep(0.5)

    return results

if __name__ == "__main__":
    all_results = []

    all_results += test_batch(TRADITIONAL_SPORTSBOOK_QUESTIONS[:8], "Live Odds")
    all_results += test_batch(STRATEGY_QUESTIONS[:6], "Strategy")
    all_results += test_batch(CONTEXTUAL_QUESTIONS[:4], "Contextual")
    all_results += test_batch(MULTI_PART_QUESTIONS[:2], "Multi-Part")

    # Summary
    total = len(all_results)
    good = sum(1 for r in all_results if r.get('success'))
    avg_time = sum(r.get('duration', 0) for r in all_results if 'duration' in r) / len([r for r in all_results if 'duration' in r])

    print(f"\n{'='*80}")
    print(f"FINAL SCORE - {MODEL}")
    print('='*80)
    print(f"✓ Success Rate: {good}/{total} ({good/total*100:.0f}%)")
    print(f"⚡ Avg Speed: {avg_time:.1f}s")
