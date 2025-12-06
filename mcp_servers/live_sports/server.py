from mcp.server.fastmcp import FastMCP
import httpx
import os
from typing import List, Dict, Any
from datetime import datetime, timedelta

# Initialize FastMCP server
mcp = FastMCP("LiveSportsData")

# Configuration
API_KEY = os.getenv("ODDS_API_KEY")
BASE_URL = "https://api.the-odds-api.com/v4/sports"

@mcp.tool()
async def list_sports() -> List[str]:
    """List all available sports that have live odds data. Use this to discover valid sport keys before calling get_odds."""
    if not API_KEY:
         return ["Error: ODDS_API_KEY environment variable not set. Please set it to use live data."]

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{BASE_URL}/?apiKey={API_KEY}")
            resp.raise_for_status()
            data = resp.json()
            return [sport["key"] for sport in data]
        except Exception as e:
            return [f"Error fetching sports: {str(e)}"]

@mcp.tool()
async def get_odds(sport: str, team: str, region: str = "us", markets: str = "h2h,spreads,totals") -> str:
    """[LIVE ODDS ONLY] Get current betting lines for a SPECIFIC TEAM's next game. USER MUST ASK ABOUT A SPECIFIC TEAM (e.g. 'Saints odds?', 'Chiefs spread?'). DO NOT use for strategy/concept questions."""

    # Validation: Reject if team is empty/generic
    if not team or len(team) < 3:
        return "ERROR: get_odds() requires a specific team name (e.g., 'Saints', 'Chiefs', 'Bills'). If you're answering a general/conceptual question, use search_guides() instead."

    if not API_KEY:
        return "ERROR: ODDS_API_KEY not set. Cannot fetch live odds."

    # Sanitize markets input (remove spaces)
    markets = markets.replace(" ", "")

    async with httpx.AsyncClient() as client:
        try:
            url = f"{BASE_URL}/{sport}/odds/"
            params = {
                "apiKey": API_KEY,
                "regions": region,
                "markets": markets,
                "oddsFormat": "american"
            }

            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

            if not data:
                return f"No live odds currently available for {sport}."

            # Filter by team if specified
            if team:
                team_lower = team.lower()
                filtered_games = []
                for game in data:
                    home = game.get('home_team', '').lower()
                    away = game.get('away_team', '').lower()
                    if team_lower in home or team_lower in away:
                        filtered_games.append(game)

                if not filtered_games:
                    return f"No games found for '{team}' in {sport}. Check the team name and try again."

                # If multiple games found, sort by time and take the next upcoming game
                if len(filtered_games) > 1:
                    filtered_games.sort(key=lambda g: g.get('commence_time', ''))
                    data = [filtered_games[0]]
                    output_suffix = f"\n\nNote: Found {len(filtered_games)} upcoming games for {team}. Showing the next game only."
                else:
                    data = filtered_games
                    output_suffix = ""
            else:
                output_suffix = ""

            # Format the output
            output = f"[REAL-TIME ODDS from The Odds API]\n\n"

            for game_idx, game in enumerate(data, 1):
                home = game.get('home_team')
                away = game.get('away_team')
                time = game.get('commence_time')

                output += f"GAME {game_idx}: {away} @ {home}\n"
                output += f"Time: {time}\n\n"

                bookmakers = game.get('bookmakers', [])[:2]

                for bookie_idx, bookie in enumerate(bookmakers, 1):
                    output += f"Book {bookie_idx}: {bookie['title']}\n"

                    for market in bookie['markets']:
                        key = market['key']

                        if key == 'h2h':
                            for outcome in market['outcomes']:
                                output += f"  {outcome['name']}: {outcome['price']:+d}\n"

                        elif key == 'spreads':
                            for outcome in market['outcomes']:
                                point = outcome.get('point', 0)
                                price = outcome['price']
                                output += f"  {outcome['name']} {point:+.1f} ({price:+d})\n"

                        elif key == 'totals':
                            point = market['outcomes'][0].get('point') if market['outcomes'] else None
                            output += f"  Total: {point} "
                            for outcome in market['outcomes']:
                                output += f"| {outcome['name']}: {outcome['price']:+d} "
                            output += "\n"

                    output += "\n"

            return output.strip() + ("\n\n" + output_suffix if output_suffix else "")

        except Exception as e:
            return f"Error fetching odds: {str(e)}"


@mcp.tool()
async def get_weekend_slate(sport: str = "americanfootball_nfl", region: str = "us") -> str:
    """
    [WEEKEND ANALYSIS] Get ALL upcoming games with full odds for the weekend.
    Use this when user asks "What's good this weekend?", "Best bets?", "Any opportunities?".
    Returns all games with spreads, totals, and moneylines for analysis.
    """
    if not API_KEY:
        return "ERROR: ODDS_API_KEY not set. Cannot fetch live odds."

    async with httpx.AsyncClient() as client:
        try:
            url = f"{BASE_URL}/{sport}/odds/"
            params = {
                "apiKey": API_KEY,
                "regions": region,
                "markets": "h2h,spreads,totals",
                "oddsFormat": "american"
            }

            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

            if not data:
                return f"No upcoming games found for {sport}."

            # Sort by game time
            data.sort(key=lambda g: g.get('commence_time', ''))

            output = f"[FULL WEEKEND SLATE - {len(data)} GAMES]\n"
            output += f"Sport: {sport.upper()}\n"
            output += "=" * 60 + "\n\n"

            for game_idx, game in enumerate(data, 1):
                home = game.get('home_team')
                away = game.get('away_team')
                time = game.get('commence_time', 'TBD')

                # Parse time for readability
                try:
                    dt = datetime.fromisoformat(time.replace('Z', '+00:00'))
                    time_str = dt.strftime("%a %m/%d %I:%M%p ET")
                except:
                    time_str = time

                output += f"GAME {game_idx}: {away} @ {home}\n"
                output += f"Kickoff: {time_str}\n"

                # Get consensus line from first bookmaker
                bookmakers = game.get('bookmakers', [])
                if bookmakers:
                    bookie = bookmakers[0]
                    output += f"Lines ({bookie['title']}):\n"

                    spread_home = None
                    spread_away = None
                    ml_home = None
                    ml_away = None
                    total = None

                    for market in bookie['markets']:
                        if market['key'] == 'spreads':
                            for outcome in market['outcomes']:
                                if outcome['name'] == home:
                                    spread_home = f"{outcome.get('point', 0):+.1f} ({outcome['price']:+d})"
                                else:
                                    spread_away = f"{outcome.get('point', 0):+.1f} ({outcome['price']:+d})"

                        elif market['key'] == 'h2h':
                            for outcome in market['outcomes']:
                                if outcome['name'] == home:
                                    ml_home = f"{outcome['price']:+d}"
                                else:
                                    ml_away = f"{outcome['price']:+d}"

                        elif market['key'] == 'totals':
                            if market['outcomes']:
                                total = market['outcomes'][0].get('point')

                    output += f"  {away}: {spread_away or 'N/A'} | ML: {ml_away or 'N/A'}\n"
                    output += f"  {home}: {spread_home or 'N/A'} | ML: {ml_home or 'N/A'}\n"
                    output += f"  Total: {total or 'N/A'}\n"

                    # Flag KEY NUMBERS
                    try:
                        if spread_home:
                            spread_val = float(spread_home.split()[0])
                            if abs(spread_val) in [3.0, 3.5, 7.0, 7.5]:
                                output += f"  ⚠️ KEY NUMBER ALERT: Spread near 3 or 7\n"
                    except:
                        pass

                output += "-" * 40 + "\n\n"

            output += "\n[END OF SLATE]\n"
            output += "Use this data to identify:\n"
            output += "- Key number opportunities (spreads at 3 or 7)\n"
            output += "- Large spreads for teasers\n"
            output += "- High/low totals for weather impact\n"
            output += "- Potential Wong teaser candidates\n"

            return output

        except Exception as e:
            return f"Error fetching weekend slate: {str(e)}"


@mcp.tool()
async def get_value_finder(sport: str = "americanfootball_nfl") -> str:
    """
    [VALUE SCANNER] Scan for key numbers, large underdogs, and potential value spots.
    """
    if not API_KEY:
        return "ERROR: ODDS_API_KEY not set."

    async with httpx.AsyncClient() as client:
        try:
            url = f"{BASE_URL}/{sport}/odds/"
            params = {
                "apiKey": API_KEY,
                "regions": "us",
                "markets": "spreads,h2h,totals",
                "oddsFormat": "american"
            }

            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

            if not data:
                return f"No games available for {sport}."

            output = f"[VALUE FINDER REPORT - {sport.upper()}]\n"
            output += "=" * 50 + "\n\n"

            key_numbers = []
            big_dogs = []
            low_totals = []
            high_totals = []

            for game in data:
                home = game.get('home_team')
                away = game.get('away_team')
                bookmakers = game.get('bookmakers', [])
                if not bookmakers: continue

                # Use first book as reference
                bookie = bookmakers[0]

                for market in bookie['markets']:
                    if market['key'] == 'spreads':
                        for outcome in market['outcomes']:
                            spread = outcome.get('point', 0)
                            if abs(spread) in [3.0, 7.0, 10.0] and "football" in sport:
                                key_numbers.append(f"{outcome['name']} {spread:+.1f} (Key Number)")

                    elif market['key'] == 'h2h':
                        for outcome in market['outcomes']:
                            price = outcome.get('price', 0)
                            if price >= 200:
                                big_dogs.append(f"{outcome['name']} ML {price:+d} (Implied: {100/(price+100)*100:.1f}%)")

                    elif market['key'] == 'totals':
                        total = market['outcomes'][0].get('point')
                        if total and total < 38 and "football" in sport:
                            low_totals.append(f"{away}@{home}: Total {total} (Low)")
                        elif total and total > 55 and "football" in sport:
                            high_totals.append(f"{away}@{home}: Total {total} (High)")

            if key_numbers:
                output += "🔑 KEY NUMBER ALERTS (3, 7, 10):\n" + "\n".join(key_numbers[:10]) + "\n\n"

            if big_dogs:
                output += "🐶 BIG UNDERDOGS (> +200):\n" + "\n".join(big_dogs[:10]) + "\n\n"

            if low_totals:
                output += "📉 LOW TOTALS (< 38):\n" + "\n".join(low_totals) + "\n\n"

            if high_totals:
                output += "🔥 HIGH TOTALS (> 55):\n" + "\n".join(high_totals) + "\n\n"

            if not (key_numbers or big_dogs or low_totals or high_totals):
                output += "No specific value signals found based on simple heuristics.\n"

            return output

        except Exception as e:
            return f"Error scanning for value: {str(e)}"


@mcp.tool()
async def find_teaser_candidates(sport: str = "americanfootball_nfl") -> str:
    """
    [WONG TEASER FINDER] Automatically find games that qualify for Wong teasers.
    Wong criteria: Favorites -7.5 to -8.5 (tease to -1.5/-2.5) OR Underdogs +1.5 to +2.5 (tease to +7.5/+8.5).
    """
    if not API_KEY:
        return "ERROR: ODDS_API_KEY not set."

    async with httpx.AsyncClient() as client:
        try:
            url = f"{BASE_URL}/{sport}/odds/"
            params = {
                "apiKey": API_KEY,
                "regions": "us",
                "markets": "spreads",
                "oddsFormat": "american"
            }

            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

            if not data:
                return "No games available."

            wong_favorites = []
            wong_dogs = []

            for game in data:
                home = game.get('home_team')
                away = game.get('away_team')
                time = game.get('commence_time', 'TBD')

                bookmakers = game.get('bookmakers', [])
                if not bookmakers:
                    continue

                for market in bookmakers[0]['markets']:
                    if market['key'] == 'spreads':
                        for outcome in market['outcomes']:
                            spread = outcome.get('point', 0)
                            team = outcome['name']

                            # Wong Favorite: -7.5 to -8.5 → tease to -1.5 to -2.5
                            if -8.5 <= spread <= -7.5:
                                wong_favorites.append({
                                    'team': team,
                                    'opponent': home if team == away else away,
                                    'spread': spread,
                                    'teased': spread + 6,
                                    'time': time,
                                    'matchup': f"{away} @ {home}"
                                })

                            # Wong Dog: +1.5 to +2.5 → tease to +7.5 to +8.5
                            elif 1.5 <= spread <= 2.5:
                                wong_dogs.append({
                                    'team': team,
                                    'opponent': home if team == away else away,
                                    'spread': spread,
                                    'teased': spread + 6,
                                    'time': time,
                                    'matchup': f"{away} @ {home}"
                                })

            output = "[WONG TEASER CANDIDATES]\n"
            output += "=" * 50 + "\n\n"

            if wong_favorites:
                output += "🔥 QUALIFYING FAVORITES (Tease DOWN through 3 and 7):\n"
                for wf in wong_favorites:
                    output += f"  • {wf['team']} {wf['spread']:+.1f} → {wf['teased']:+.1f}\n"
                    output += f"    {wf['matchup']}\n\n"
            else:
                output += "No qualifying favorites (-7.5 to -8.5) found.\n\n"

            if wong_dogs:
                output += "🔥 QUALIFYING UNDERDOGS (Tease UP through 3 and 7):\n"
                for wd in wong_dogs:
                    output += f"  • {wd['team']} {wd['spread']:+.1f} → {wd['teased']:+.1f}\n"
                    output += f"    {wd['matchup']}\n\n"
            else:
                output += "No qualifying underdogs (+1.5 to +2.5) found.\n\n"

            if wong_favorites and wong_dogs:
                output += "\n💡 PAIRING SUGGESTION:\n"
                output += f"  {wong_favorites[0]['team']} {wong_favorites[0]['teased']:+.1f} + {wong_dogs[0]['team']} {wong_dogs[0]['teased']:+.1f}\n"
                output += "  This 2-team 6-point teaser qualifies as a Wong Teaser!\n"

            return output

        except Exception as e:
            return f"Error finding teaser candidates: {str(e)}"


@mcp.tool()
def get_betting_glossary() -> Dict[str, str]:
    """Returns a glossary of common betting terms."""
    return {
        "Moneyline": "A bet on which team will win the game outright.",
        "Spread": "A handicap given to the favorite team to level the playing field.",
        "Over/Under": "A bet on the total score of the game being over or under a set number.",
        "Parlay": "A single bet that links together two or more individual wagers for a high payout.",
        "Prop Bet": "A bet on specific events within a game, not necessarily the final outcome."
    }

if __name__ == "__main__":
    mcp.run()
