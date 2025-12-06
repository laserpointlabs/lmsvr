import sys
import os

sys.path.append(os.getcwd())

# Test the search function directly
from mcp_servers.betting_context.server import search_guides, list_guides, read_guide

print("Available Guides:")
guides = list_guides()
for g in guides:
    print(f"  - {g}")

print("\n" + "="*80)
print("Testing Search Function")
print("="*80)

test_queries = [
    "Why is 3 important in NFL betting",
    "How does wind affect NFL totals",
    "lookahead spot",
    "rain betting under",
    "bye week"
]

for query in test_queries:
    print(f"\nQuery: '{query}'")
    result = search_guides(query)
    print(f"Result length: {len(result)} chars")
    print(f"Preview: {result[:200]}...")
