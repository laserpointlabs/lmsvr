"""
OpenAI-specific chat handler with MCP tool integration.
"""
import logging
import json
from typing import Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


async def handle_openai_chat(request, messages_with_system, tools, mcp_manager, openai_chat_completions):
    """
    Handle OpenAI chat requests with MCP tool calling.

    Args:
        request: ChatRequest object
        messages_with_system: Messages with system prompt already injected
        tools: List of tools in Ollama format (needs conversion to OpenAI format)
        mcp_manager: MCP manager instance for executing tools
        openai_chat_completions: Function to call OpenAI API

    Returns:
        dict: Response in Ollama format for frontend compatibility
    """
    # Convert MCP tools to OpenAI format
    openai_tools = []
    if tools:
        for t in tools:
            openai_tools.append({
                "type": "function",
                "function": t["function"]
            })

    # Initial call to OpenAI
    response = await openai_chat_completions(
        model=request.model,
        messages=messages_with_system,
        stream=False,
        tools=openai_tools if openai_tools else None
    )

    response_message = response["choices"][0]["message"]
    tool_calls = response_message.get("tool_calls")

    # Loop for recursive tool calls (limit to 5 to prevent infinite loops)
    iterations = 0
    max_iterations = 5

    while tool_calls and iterations < max_iterations:
        iterations += 1
        logger.info(f"OpenAI requesting {len(tool_calls)} tool call(s) (Iteration {iterations})")

        # Important: Append the assistant's message with tool_calls to history
        # OpenAI requires this exact message object to match the tool_call_id
        messages_with_system.append(response_message)

        for tool_call in tool_calls:
            function_name = tool_call["function"]["name"]
            try:
                function_args = json.loads(tool_call["function"]["arguments"])
            except json.JSONDecodeError:
                function_args = {}

            logger.info(f"Executing tool: {function_name} with args: {function_args}")
            tool_result = await mcp_manager.execute_tool(function_name, function_args)

            messages_with_system.append({
                "tool_call_id": tool_call["id"],
                "role": "tool",
                "name": function_name,
                "content": str(tool_result)
            })

        # Call OpenAI again with tool results
        response = await openai_chat_completions(
            model=request.model,
            messages=messages_with_system,
            stream=False,
            tools=openai_tools if openai_tools else None
        )

        response_message = response["choices"][0]["message"]
        tool_calls = response_message.get("tool_calls")

    # Final content
    content = response_message.get("content", "")
    if content is None:
        content = ""

    # Convert to Ollama format for frontend compatibility
    return {
        "model": request.model,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "message": {
            "role": "assistant",
            "content": content
        },
        "done": True
    }
