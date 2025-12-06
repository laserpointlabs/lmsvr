# MCP Tool Calling: Model Compatibility

## Issue Discovered
Not all Ollama models support tool calling properly. When a model doesn't understand tool calling, it will output the tool call as **text content** instead of executing it.

## Test Results

| Model | Tool Calling Support | Result |
|-------|---------------------|--------|
| `llama3.2:latest` (3B) | ✅ **Excellent** | Successfully calls tools and returns formatted answers |
| `qwen2.5-coder:32b` | ❌ Poor | Outputs tool calls as JSON text |
| `mistral:latest` | ❌ Poor | Outputs tool calls as code |
| `llama3.2:1b` | ❌ Poor | Likely same issue (smaller model) |

## Solution Applied
1. **Updated Default Model**: Changed `docker-compose.yml` to use `llama3.2:latest` instead of `llama3.2:1b`.
2. **Frontend Fix**: Added logic to skip displaying tool_call messages in the UI.
3. **Backend Enhancement**: Added team filtering to `get_odds` tool so queries like "What are the odds for the Saints game?" return only relevant data.

## Recommended Models for Betting
- **Primary**: `llama3.2:latest` (fast, good tool support)
- **Alternative**: Test with `deepseek-r1:70b` or `qwen3-coder:30b` if you need more complex reasoning

## Usage
The frontend will now default to `llama3.2:latest`. If you have an existing session, **clear your browser's localStorage** or select the model manually from the dropdown.
