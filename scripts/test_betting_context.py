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

    print("Fetching tools...")
    tools = await mcp_manager.get_tools_ollama_format()
    print(f"Found {len(tools)} tools.")
    for tool in tools:
        print(f"- {tool['function']['name']}: {tool['function']['description']}")

    print("\nTesting list_guides...")
    result = await mcp_manager.execute_tool("list_guides", {})
    print(f"Guides: {result}")

    print("\nTesting read_guide (markdown)...")
    result = await mcp_manager.execute_tool("read_guide", {"filename": "betting_basics.md"})
    print(f"Content preview: {result[:100]}...")

    print("\nTesting search_guides...")
    result = await mcp_manager.execute_tool("search_guides", {"query": "moneyline"})
    print(f"Search result preview: {result[:100]}...")

    await mcp_manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
