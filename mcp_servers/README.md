# MCP Servers for Betting Assistant

This directory contains Model Context Protocol (MCP) servers used by the API Gateway to provide betting context and live data.

## Servers

### 1. Betting Context (`betting_context`)
Provides access to betting guides, examples, and documentation in PDF and Markdown formats.

- **Location**: `mcp_servers/betting_context/`
- **Data**: Place PDF or Markdown files in `mcp_servers/betting_context/data/`.
- **Tools**:
  - `list_guides`: List available files.
  - `read_guide`: Read a specific file.
  - `search_guides`: Keyword search across all files.

### 2. Live Sports Data (`live_sports`)
Provides live odds and upcoming game information.

- **Location**: `mcp_servers/live_sports/`
- **Configuration**: Currently uses mock data. To use real data, obtain an API Key from [The Odds API](https://the-odds-api.com/) and update `server.py`.
- **Tools**:
  - `list_sports`: List available sports.
  - `get_odds`: Get live odds for a sport.
  - `get_betting_glossary`: Common terms.

## Setup

The `api_gateway` automatically starts these servers. Ensure dependencies are installed:

```bash
pip install -r mcp_servers/betting_context/requirements.txt
pip install -r mcp_servers/live_sports/requirements.txt
```
