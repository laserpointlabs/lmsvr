from mcp.server.fastmcp import FastMCP
import httpx
from typing import Dict, List, Any, Optional

# Initialize FastMCP server
mcp = FastMCP("SportsData")

# Base URL for ESPN APIs
BASE_URL = "https://site.api.espn.com/apis/site/v2/sports"

# Sport Mappings (Internal Key -> ESPN Path)
SPORT_CONFIG = {
    "nfl": {"path": "football/nfl", "abbr": "NFL"},
    "ncaaf": {"path": "football/college-football", "abbr": "NCAAF"},
    "nba": {"path": "basketball/nba", "abbr": "NBA"},
    "ncaam": {"path": "basketball/mens-college-basketball", "abbr": "NCAAM"},
    "mlb": {"path": "baseball/mlb", "abbr": "MLB"}
}

def find_team_id(teams: List[Dict], query: str) -> Optional[Dict]:
    """Helper to find a team in the ESPN list with fuzzy matching."""
    query = query.lower().strip()

    # Common mappings
    mappings = {
        "commanders": "washington",
        "washington commanders": "washington",
        "ole miss": "mississippi",
        "southern cal": "usc",
        "nc state": "north carolina state",
    }
    if query in mappings:
        query = mappings[query]

    for t in teams:
        team = t.get("team", {})
        display_name = team.get("displayName", "").lower()
        short_name = team.get("shortDisplayName", "").lower()
        nickname = team.get("nickname", "").lower()
        location = team.get("location", "").lower()
        abbr = team.get("abbreviation", "").lower()

        if (query == display_name or
            query == short_name or
            query == nickname or
            query == abbr or
            query in display_name or
            display_name in query):
            return team

    return None

@mcp.tool()
async def get_team_stats(sport: str, team_name: str) -> str:
    """
    Get stats/record for a team in a specific sport.

    Args:
        sport: "nfl", "ncaaf", "nba", "ncaam", or "mlb"
        team_name: Name of the team (e.g. "Lakers", "Alabama", "Yankees")
    """
    sport = sport.lower()
    if sport not in SPORT_CONFIG:
        return f"Error: Sport '{sport}' not supported. Use: {', '.join(SPORT_CONFIG.keys())}"

    config = SPORT_CONFIG[sport]
    url = f"{BASE_URL}/{config['path']}/teams"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Fetch teams (limit higher for college sports)
            limit = 1000 if "college" in config['path'] else 32
            resp = await client.get(f"{url}?limit={limit}")
            if resp.status_code != 200:
                return f"Error fetching {sport.upper()} data."

            data = resp.json()
            try:
                teams = data.get("sports", [])[0].get("leagues", [])[0].get("teams", [])
            except IndexError:
                return f"Error parsing team list for {sport}."

            # Find team
            target_team = find_team_id(teams, team_name)

            if not target_team:
                return f"{config['abbr']} Team '{team_name}' not found."

            # Get detailed stats (via team ID)
            team_id = target_team.get("id")
            record_resp = await client.get(f"{url}/{team_id}")
            record_data = record_resp.json()
            team_info = record_data.get("team", {})

            # Extract Record
            record = "N/A"
            if "record" in team_info and "items" in team_info["record"]:
                items = team_info["record"]["items"]
                if items and len(items) > 0:
                    record = items[0].get("summary", "N/A")

            standing = team_info.get("standingSummary", "N/A")

            # Basic Next Game info
            game_name = "Unknown"
            game_date = "Unknown"

            next_events = team_info.get("nextEvent", [])
            if next_events and len(next_events) > 0:
                next_event = next_events[0]
                game_name = next_event.get("name", "Unknown")
                game_date = next_event.get("date", "Unknown")

            # Additional stats (vary by sport)
            # We could add rank for college
            rank = team_info.get("rank", "")
            rank_str = f" (#{rank})" if rank and rank < 99 else ""

            return f"""[REAL DATA from ESPN]
**{target_team.get('displayName')}{rank_str}** ({config['abbr']})
- **Record**: {record}
- **Standing**: {standing}
- **Next Game**: {game_name} ({game_date})
- **Stadium/Arena**: {target_team.get('venue', {}).get('name', 'Unknown')}
"""
        except Exception as e:
            return f"Error getting {sport} stats: {str(e)}"

@mcp.tool()
async def get_injuries(sport: str, team_name: str) -> str:
    """
    Get injuries/news for a team in a specific sport.

    Args:
        sport: "nfl", "ncaaf", "nba", "ncaam", or "mlb"
        team_name: Name of the team
    """
    sport = sport.lower()
    if sport not in SPORT_CONFIG:
        return f"Error: Sport '{sport}' not supported."

    config = SPORT_CONFIG[sport]
    url = f"{BASE_URL}/{config['path']}/teams"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 1. Find team ID
            limit = 1000 if "college" in config['path'] else 32
            resp = await client.get(f"{url}?limit={limit}")
            if resp.status_code != 200:
                return "Error fetching team list."

            data = resp.json()
            try:
                teams = data.get("sports", [])[0].get("leagues", [])[0].get("teams", [])
            except IndexError:
                return "Error parsing team list."

            target_team = find_team_id(teams, team_name)

            if not target_team:
                return f"Team '{team_name}' not found."

            team_id = target_team.get("id")

            # 2. Fetch team-specific news
            news_resp = await client.get(f"{url}/{team_id}/news")
            if news_resp.status_code != 200:
                 return f"Error fetching news for {team_name}."

            news_data = news_resp.json()
            articles = news_data.get("articles", [])

            relevant_news = []
            keywords = ["injury", "out", "doubtful", "questionable", "IR", "surgery", "concussion", "knee", "ankle", "hamstring", "shoulder", "arm", "transfer", "suspension"]

            for article in articles:
                headline = article.get("headline", "")
                desc = article.get("description", "")
                full_text = (headline + " " + desc).lower()

                if any(x in full_text for x in keywords):
                    relevant_news.append(f"- {headline}")

            if not relevant_news:
                return f"No major injury/roster headlines found for {target_team.get('displayName')}."

            return f"[INJURY/NEWS for {target_team.get('displayName')}]\n" + "\n".join(relevant_news[:5])

        except Exception as e:
            return f"Error fetching injuries: {str(e)}"

if __name__ == "__main__":
    mcp.run()
