from mcp.server.fastmcp import FastMCP
import httpx
import os
from typing import Dict, Any

# Initialize FastMCP server
mcp = FastMCP("NFLContext")

# ESPN has a public (unofficial) API for injuries and scores
ESPN_NFL_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")  # Optional: OpenWeather or WeatherAPI

@mcp.tool()
async def get_nfl_injuries(team: str = None) -> str:
    """
    Get current NFL injury report. Helps assess if key players are out.

    Args:
        team: Optional team name to filter (e.g., 'Chiefs', 'Saints')
    """
    async with httpx.AsyncClient() as client:
        try:
            # ESPN provides injury data via their unofficial API
            resp = await client.get(f"{ESPN_NFL_URL}/news", timeout=10.0)

            if resp.status_code == 200:
                data = resp.json()
                articles = data.get("articles", [])

                # Filter injury-related news
                injury_news = []
                for article in articles[:20]:
                    headline = article.get("headline", "")
                    description = article.get("description", "")

                    # Check if it's injury-related
                    if any(word in (headline + description).lower() for word in ['injury', 'injured', 'out', 'questionable', 'doubtful', 'ir']):
                        if team:
                            if team.lower() in (headline + description).lower():
                                injury_news.append(f"• {headline}")
                        else:
                            injury_news.append(f"• {headline}")

                if injury_news:
                    return "\n".join(injury_news[:10])
                else:
                    return f"No significant injury news found" + (f" for {team}" if team else "")
            else:
                return "Unable to fetch injury data at this time."
        except Exception as e:
            return f"Error fetching injuries: {str(e)}"

@mcp.tool()
async def get_matchup_analysis(home_team: str, away_team: str) -> str:
    """
    Get basic matchup context for an NFL game (records, recent performance).

    Args:
        home_team: Home team name (e.g., 'Chiefs')
        away_team: Away team name (e.g., 'Bills')
    """
    # This is a simplified version - in production you'd call ESPN or another stats API
    async with httpx.AsyncClient() as client:
        try:
            # ESPN scoreboard gives us team records and recent games
            resp = await client.get(f"{ESPN_NFL_URL}/scoreboard", timeout=10.0)

            if resp.status_code == 200:
                data = resp.json()
                events = data.get("events", [])

                # Find the game
                for event in events:
                    competitions = event.get("competitions", [])
                    for comp in competitions:
                        competitors = comp.get("competitors", [])

                        team_names = [c.get("team", {}).get("displayName", "") for c in competitors]

                        if any(home_team.lower() in tn.lower() for tn in team_names) and \
                           any(away_team.lower() in tn.lower() for tn in team_names):
                            # Found the game
                            output = f"Matchup: {away_team} @ {home_team}\n"
                            for competitor in competitors:
                                team = competitor.get("team", {})
                                record = competitor.get("records", [{}])[0].get("summary", "Unknown")
                                output += f"  {team.get('displayName')}: {record}\n"
                            return output

                return f"Game not found in upcoming schedule: {away_team} @ {home_team}"
            else:
                return "Unable to fetch matchup data."
        except Exception as e:
            return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run()
