from mcp.server.fastmcp import FastMCP
import httpx
import json
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

# Initialize FastMCP server
mcp = FastMCP("Weather")

# Data
DATA_DIR = Path(__file__).parent / "data"
STADIUMS_FILE = DATA_DIR / "stadiums.json"

def load_stadiums() -> Dict[str, Any]:
    if STADIUMS_FILE.exists():
        with open(STADIUMS_FILE, 'r') as f:
            return json.load(f)
    return {}

STADIUMS = load_stadiums()

def find_stadium(team_name: str) -> Optional[Dict[str, Any]]:
    """Find stadium data by team name."""
    team_key = team_name.strip()

    # Try exact match (e.g. "KC")
    if team_key in STADIUMS:
        data = STADIUMS[team_key]
        if "ref" in data: # It's an alias
            return STADIUMS.get(data["ref"])
        return data

    # Try partial match in names/keys
    team_lower = team_name.lower()

    # Check specific team mappings first (from the file keys)
    for key, data in STADIUMS.items():
        if key.lower() in team_lower or team_lower in key.lower():
             if "ref" in data:
                 return STADIUMS.get(data["ref"])
             return data

    return None

@mcp.tool()
async def get_game_weather(home_team: str, game_time_iso: str = None) -> str:
    """
    Get weather forecast for a specific NFL game based on the home team's stadium.

    Args:
        home_team: Name of the home team (e.g., "Bills", "Kansas City", "BUF").
        game_time_iso: ISO 8601 formatted game time (e.g., "2025-12-07T18:00:00Z").
                       If None, defaults to current time + 3 hours (approx next game).
    """
    stadium = find_stadium(home_team)
    if not stadium:
        return f"Error: Could not locate stadium for '{home_team}'."

    location_name = f"{stadium['name']} ({stadium['city']}, {stadium['state']})"
    stadium_type = stadium.get("type", "Outdoor")

    # Check for Dome
    if stadium_type == "Dome":
        return f"🏟️ **{location_name}**\n- **Type**: Dome (Indoors)\n- **Forecast**: Climate Controlled (No weather impact)."

    # Parse time
    try:
        if game_time_iso:
            game_dt = datetime.fromisoformat(game_time_iso.replace('Z', '+00:00'))
        else:
            game_dt = datetime.now(timezone.utc)
    except ValueError:
        return f"Error: Invalid date format '{game_time_iso}'. Use ISO 8601."

    # Call Open-Meteo
    lat = stadium["lat"]
    lon = stadium["lon"]

    async with httpx.AsyncClient() as client:
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": lat,
                "longitude": lon,
                "hourly": "temperature_2m,precipitation_probability,windspeed_10m,winddirection_10m,weathercode",
                "temperature_unit": "fahrenheit",
                "windspeed_unit": "mph",
                "precipitation_unit": "inch",
                "timezone": "auto"
            }

            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return f"Error fetching weather from Open-Meteo: {resp.status_code}"

            data = resp.json()
            hourly = data.get("hourly", {})
            times = hourly.get("time", [])

            # Find closest hour index
            # Open-Meteo returns ISO local/UTC strings
            # We need to match the game_dt

            # Simplification: Find index where time string matches closest
            # Convert game_dt to string prefix match
            target_str = game_dt.strftime("%Y-%m-%dT%H")

            idx = -1
            for i, t_str in enumerate(times):
                if t_str.startswith(target_str):
                    idx = i
                    break

            # Fallback if not found (e.g. game is next week and forecast not out, or passed)
            if idx == -1:
                # Just grab the first one if it's "now", or return error
                if not game_time_iso:
                    idx = 0 # Current forecast
                else:
                    return f"Forecast data not available for {game_time_iso} (Open-Meteo usually provides 7 days)."

            # Extract data
            temp = hourly["temperature_2m"][idx]
            precip_prob = hourly["precipitation_probability"][idx]
            wind_speed = hourly["windspeed_10m"][idx]
            wind_dir = hourly["winddirection_10m"][idx]
            wcode = hourly["weathercode"][idx]

            # Weather code interpretation
            conditions = "Clear"
            if wcode > 0: conditions = "Cloudy/Overcast"
            if wcode >= 50: conditions = "Drizzle/Rain"
            if wcode >= 70: conditions = "Snow"
            if wcode >= 95: conditions = "Thunderstorm"

            # Analysis for Betting
            impact = "Neutral"
            if wind_speed >= 15:
                impact = "📉 **UNDER LEAN** (High Winds)"
            elif precip_prob >= 50 and conditions in ["Snow", "Drizzle/Rain"]:
                impact = "📉 **SLIGHT UNDER LEAN** (Precipitation)"
            elif temp <= 20:
                impact = "🥶 **COLD GAME** (Run heavy?)"
            elif temp >= 90:
                impact = "🔥 **HEAT FACTOR** (Fatigue?)"

            return f"""🌤️ **Weather Forecast for {location_name}**
**Time**: {times[idx]}
**Type**: {stadium_type}

- **Temp**: {temp}°F
- **Wind**: {wind_speed} mph (Dir: {wind_dir}°)
- **Precip**: {precip_prob}% chance ({conditions})

**Betting Impact**: {impact}"""

        except Exception as e:
            return f"Error processing weather: {str(e)}"

if __name__ == "__main__":
    mcp.run()
