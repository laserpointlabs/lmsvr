# Matchup & Recommendation Engine

This folder contains the `nfl_data` MCP server which connects to real sports data sources (ESPN) to provide context for betting recommendations.

## Tools
1.  `get_nfl_team_stats(team_name)`: Fetches real-time record, standing, and next game info.
2.  `get_nfl_injuries(team_name)`: Scans major news headlines for injury updates.

## Usage in Recommendation System
When a user asks "Who should I bet on in the Chiefs game?", the system now:
1.  **get_odds**: Gets the line (e.g., Chiefs -3.5).
2.  **get_nfl_team_stats**: Checks if Chiefs are hot (e.g., 10-2 record).
3.  **get_nfl_injuries**: Checks if Mahomes is hurt.
4.  **Synthesizes**: "Chiefs are favored by 3.5, BUT Mahomes is questionable. Risky bet."
