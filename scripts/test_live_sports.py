import asyncio
import sys
import os

# Add parent dir to path
sys.path.append(os.getcwd())

# Mock environment variables if needed
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"

try:
    from api_gateway.mcp_manager import mcp_manager
except ImportError:
    print("Error importing mcp_manager. Make sure dependencies are installed.")
    sys.exit(1)

async def main():
    print("Starting servers...")
    await mcp_manager.start_servers()

    # CRITICAL: Must fetch tools to populate tools_map
    print("Fetching tools to populate registry...")
    await mcp_manager.get_tools_ollama_format()

    print("\n--- Testing Live Sports Server (MOCK DATA) ---")

    print("\n1. Listing Available Sports...")
    sports = await mcp_manager.execute_tool("list_sports", {})
    print(f"Sports: {sports}")

    print("\n2. Getting Odds for NFL (Mock Data)...")
    odds = await mcp_manager.execute_tool("get_odds", {"sport": "americanfootball_nfl"})
    print(f"Odds Response:\n{odds}")

    print("\n3. Getting Betting Glossary...")
    glossary = await mcp_manager.execute_tool("get_betting_glossary", {})
    print(f"Glossary Preview: {str(glossary)[:100]}...")

    await mcp_manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
