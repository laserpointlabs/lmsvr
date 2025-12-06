from mcp.server.fastmcp import FastMCP
import httpx
import json
from typing import List, Dict, Any
from datetime import datetime, timedelta
import asyncio

# Initialize FastMCP server
mcp = FastMCP("PrizePicksData")

# Cache configuration
CACHE_DURATION = 300  # 5 minutes in seconds
cache = {
    "projections": None,
    "last_updated": None
}

# PrizePicks Internal API (Reverse Engineered)
# DISCLAIMER: This uses PrizePicks' internal API which may violate their Terms of Use.
# Use at your own risk. Consider using a third-party data provider for production.
BASE_URL = "https://api.prizepicks.com"

async def fetch_projections_from_api() -> List[Dict[str, Any]]:
    """Fetch player projections from PrizePicks internal API."""
    async with httpx.AsyncClient() as client:
        try:
            # Fetch projections (this endpoint returns all active player props)
            resp = await client.get(
                f"{BASE_URL}/projections",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json"
                },
                timeout=15.0
            )

            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", [])
            else:
                return []
        except Exception as e:
            return []

async def get_cached_projections() -> List[Dict[str, Any]]:
    """Get projections from cache or fetch fresh if expired."""
    global cache

    now = datetime.now()

    # Check if cache is valid
    if cache["projections"] and cache["last_updated"]:
        age = (now - cache["last_updated"]).total_seconds()
        if age < CACHE_DURATION:
            return cache["projections"]

    # Fetch fresh data
    projections = await fetch_projections_from_api()
    cache["projections"] = projections
    cache["last_updated"] = now

    return projections

@mcp.tool()
async def get_prizepicks_props(sport: str = "NFL", player_name: str = None, stat_type: str = None) -> str:
    """
    Get PrizePicks player props for NFL or NCAAF. Updated every 5 minutes.

    Args:
        sport: Sport filter (NFL, NCAAF). Default NFL.
        player_name: Optional player name to filter (e.g., 'Patrick Mahomes', 'Jalen Hurts')
        stat_type: Optional stat type (e.g., 'Passing Yards', 'Rushing Yards', 'Receptions')
    """
    projections = await get_cached_projections()

    if not projections:
        return "Unable to fetch PrizePicks data at this time. The service may be unavailable or blocking requests."

    # Filter by sport
    sport_upper = sport.upper()
    filtered = [p for p in projections if p.get("league_name", "").upper() == sport_upper]

    # Filter by player if specified
    if player_name:
        player_lower = player_name.lower()
        filtered = [p for p in filtered if player_lower in p.get("description", "").lower()]

    # Filter by stat type if specified
    if stat_type:
        stat_lower = stat_type.lower()
        filtered = [p for p in filtered if stat_lower in p.get("stat_type", "").lower()]

    if not filtered:
        return f"No PrizePicks props found for {sport}" + (f" player: {player_name}" if player_name else "") + (f" stat: {stat_type}" if stat_type else "")

    # Format output
    cache_age = (datetime.now() - cache["last_updated"]).total_seconds() if cache["last_updated"] else 0
    output = f"[PRIZEPICKS PROPS - Updated {int(cache_age)}s ago]\n\n"

    # Group by player
    by_player = {}
    for proj in filtered[:30]:  # Limit to 30 props
        player = proj.get("description", "Unknown")
        if player not in by_player:
            by_player[player] = []
        by_player[player].append(proj)

    for player, props in list(by_player.items())[:15]:  # Max 15 players
        output += f"**{player}**\n"
        for prop in props[:3]:  # Max 3 props per player
            stat = prop.get("stat_type", "Unknown")
            line = prop.get("line_score", "N/A")
            output += f"  - {stat}: {line}\n"
        output += "\n"

    return output.strip()

@mcp.tool()
def prizepicks_strategy() -> Dict[str, str]:
    """Get tips for building PrizePicks lineups and prop betting strategy."""
    return {
        "Correlation": "Stack QB + their WR for correlated props (if QB has big game, WR likely does too)",
        "Leverage": "In tournaments, take contrarian props (low ownership) for higher upside",
        "Variance": "Player props have HIGHER variance than game spreads. Expect more volatility.",
        "Overs vs Unders": "PrizePicks lines are sharp. Don't blindly take all overs or all unders.",
        "Research": "Check injury reports, weather, matchups before locking in props"
    }

if __name__ == "__main__":
    mcp.run()
