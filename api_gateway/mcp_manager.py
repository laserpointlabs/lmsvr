import asyncio
import os
import sys
import logging
from contextlib import AsyncExitStack
from typing import Dict, List, Any, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

class MCPManager:
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.exit_stack = AsyncExitStack()
        self.tools_map: Dict[str, str] = {} # Maps tool name to server name

    async def start_servers(self):
        """Start all configured MCP servers."""
        # Define servers
        # We assume the mcp_servers directory is in the workspace root
        workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

        servers = {
            "betting_context": {
                "command": sys.executable,
                "args": [os.path.join(workspace_root, "mcp_servers/betting_context/server.py")],
                "env": os.environ.copy()
            },
            "live_sports": {
                "command": sys.executable,
                "args": [os.path.join(workspace_root, "mcp_servers/live_sports/server.py")],
                "env": os.environ.copy()
            },
            "prizepicks": {
                "command": sys.executable,
                "args": [os.path.join(workspace_root, "mcp_servers/prizepicks/server.py")],
                "env": os.environ.copy()
            },
            "sports_data": {
                "command": sys.executable,
                "args": [os.path.join(workspace_root, "mcp_servers/sports_data/server.py")],
                "env": os.environ.copy()
            },
            "betting_monitor": {
                "command": sys.executable,
                "args": [os.path.join(workspace_root, "mcp_servers/betting_monitor/server.py")],
                "env": os.environ.copy()
            },
            "weather": {
                "command": sys.executable,
                "args": [os.path.join(workspace_root, "mcp_servers/weather/server.py")],
                "env": os.environ.copy()
            }
        }

        for name, config in servers.items():
            try:
                logger.info(f"Starting MCP server: {name} with cmd: {config['command']} {config['args']}")

                # Create server parameters
                server_params = StdioServerParameters(
                    command=config["command"],
                    args=config["args"],
                    env=config.get("env")
                )

                # Connect to server
                read, write = await self.exit_stack.enter_async_context(
                    stdio_client(server_params)
                )

                session = await self.exit_stack.enter_async_context(
                    ClientSession(read, write)
                )

                await session.initialize()
                self.sessions[name] = session
                logger.info(f"Connected to MCP server: {name}")

            except Exception as e:
                logger.error(f"Failed to connect to MCP server {name}: {e}", exc_info=True)

    async def get_tools_ollama_format(self) -> List[Dict[str, Any]]:
        """Get all tools from all servers and format for Ollama."""
        ollama_tools = []
        self.tools_map = {} # Reset cache

        for server_name, session in self.sessions.items():
            try:
                result = await session.list_tools()
                for tool in result.tools:
                    # Format for Ollama
                    ollama_tool = {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema
                        }
                    }
                    ollama_tools.append(ollama_tool)

                    # Map tool to server
                    self.tools_map[tool.name] = server_name
            except Exception as e:
                logger.error(f"Error fetching tools from {server_name}: {e}")

        return ollama_tools

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool on the appropriate server."""
        server_name = self.tools_map.get(tool_name)

        if not server_name:
            return f"Error: Tool {tool_name} not found."

        session = self.sessions.get(server_name)
        if not session:
            return f"Error: Server {server_name} not connected."

        try:
            logger.info(f"Executing tool {tool_name} on server {server_name}")
            result = await session.call_tool(tool_name, arguments)

            # Return content from the result
            output = []
            for content in result.content:
                if content.type == "text":
                    output.append(content.text)
                # Handle other content types if needed
            return "\n".join(output)

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            return f"Error executing tool {tool_name}: {str(e)}"

    async def cleanup(self):
        """Close all connections."""
        await self.exit_stack.aclose()

# Global instance
mcp_manager = MCPManager()
