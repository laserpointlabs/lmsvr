import requests
import json

BASE_URL = "http://localhost:8001"
API_KEY = "sk_p_9R0Dm4kfOLxD7zjLLX8A"
MODEL = "granite4:3b"

# Test PrizePicks integration
questions = [
    # Traditional NFL
    ("NFL", "What are the odds for the Chiefs game?"),

    # NCAA
    ("NCAA", "What's the spread on the Alabama game?"),

    # PrizePicks Props
    ("PRIZEPICKS", "What are Patrick Mahomes passing yards props?"),
    ("PRIZEPICKS", "Show me the top QB passing props for Sunday."),

    # Parlay
    ("PARLAY", "Should I parlay Chiefs -3.5 and Bills -5?"),
]

print("FULL GAMBLER TEST - NFL, NCAA, PrizePicks\n")
print(f"Model: {MODEL}")
print('='*80)

for category, question in questions:
    print(f"\n[{category}] {question}")

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": question}],
        "stream": False
    }

    resp = requests.post(
        f"{BASE_URL}/api/chat",
        json=payload,
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=45
    )

    if resp.status_code == 200:
        content = resp.json().get("message", {}).get("content", "")
        print(f"  ✓ ({len(content)} chars): {content[:200]}...")
    else:
        print(f"  ❌ HTTP {resp.status_code}")

print("\n" + "="*80)
print("Ready for full test? System now supports:")
print("  - NFL odds (DraftKings, FanDuel, BetUS)")
print("  - NCAA odds (via The Odds API)")
print("  - PrizePicks player props (5-min cache)")
print("  - Parlay/Teaser strategy (via betting guides)")
