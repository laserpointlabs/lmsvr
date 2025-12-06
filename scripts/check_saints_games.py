#!/usr/bin/env python3
import httpx
import asyncio
import os

API_KEY = "141b6c8fb4955d31c9c808a6fde1e8da"
BASE_URL = "https://api.the-odds-api.com/v4/sports"

async def main():
    async with httpx.AsyncClient() as client:
        # Get all NFL odds
        resp = await client.get(
            f"{BASE_URL}/americanfootball_nfl/odds/",
            params={
                "apiKey": API_KEY,
                "regions": "us",
                "markets": "h2h,spreads,totals",
                "oddsFormat": "american"
            }
        )

        data = resp.json()

        # Filter for Saints games
        saints_games = []
        for game in data:
            home = game.get('home_team', '').lower()
            away = game.get('away_team', '').lower()
            if 'saints' in home or 'saints' in away:
                saints_games.append(game)

        print(f"Found {len(saints_games)} Saints game(s):")
        for game in saints_games:
            print(f"  {game['away_team']} @ {game['home_team']} - {game['commence_time']}")

if __name__ == "__main__":
    asyncio.run(main())
