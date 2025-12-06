# Betting Assistant MCP Integration - System Summary

## Overview
This system provides a betting assistant powered by two MCP servers:
1. **Betting Context**: Access to expert guides (PDF/Markdown) on NFL/NCAA strategies
2. **Live Sports Data**: Real-time odds from The Odds API

## Current Configuration

### Default Model: `granite4:3b`
**Performance Metrics** (20-question comprehensive test):
- ✅ **Success Rate**: 70% (14/20 correct answers)
- ⚡ **Avg Response Time**: 4.7s
- 🎯 **Tool Execution**: 100% reliable (no tool call leaks)
- 📊 **Data Usage**: 40% live odds, 35% expert guides

### Alternative Model: `qwen2.5:32b`
- ✅ Success Rate: 75% (slightly better accuracy)
- ⏱️ Avg Response Time: 20s (4x slower)
- Best for: Complex multi-part questions requiring deep analysis

## Betting Knowledge Base

### Files in `mcp_servers/betting_context/data/`:
1. **nfl_betting_strategy.md** - Key numbers (3, 7), QB value, HFA, situational spots
2. **ncaa_betting_strategy.md** - Power ratings, recruiting, motivation, weather impact
3. **bankroll_management.md** - Unit sizing, Kelly Criterion, risk mitigation
4. **betting_glossary.md** - CLV, steam, sharp/square, lookahead spots
5. **betting_basics.md** - Moneyline, spread, totals explained

### Live Sports API: The Odds API
- **Endpoint**: `https://api.the-odds-api.com/v4/sports`
- **Free Tier**: 500 requests/month
- **Sports Supported**: NFL, NCAAF, NBA, MLB, NHL, EPL
- **Markets**: Moneyline (h2h), Spreads, Totals, Futures

## Test Results by Category

### Live Odds Queries (8 questions)
- ✓ "What are the odds for the Chiefs game?" → **SUCCESS** (3.0s)
- ✓ "Who is favored in the Bills game?" → **SUCCESS** (3.3s)
- ✓ "What's the spread on the 49ers game?" → **SUCCESS** (3.4s)
- ✓ "Alabama odds?" → **SUCCESS** (3.6s - NCAA working!)
- ⚠ "Cowboys vs Eagles over/under?" → Partial (missing context)

**Success Rate**: 6/8 (75%)

### Strategy & Bankroll (6 questions)
- ✓ "Kelly Criterion?" → **EXCELLENT** (mentions formula, Quarter-Kelly)
- ✓ "$1000 bankroll sizing?" → **EXCELLENT** (recommends 1-2% units)
- ✓ "Why is 3 important in NFL?" → **EXCELLENT** (cites 15%, key number, FG)
- ✓ "Flat vs Variable betting?" → **SUCCESS**

**Success Rate**: 6/6 (100%)

### Multi-Part Analysis (2 questions)
- ✓ "Chiefs -7 with $500 bankroll?" → **SUCCESS** (analyzed risk + sizing)
- ✓ "Saints spread vs moneyline value?" → **SUCCESS** (compared both)

**Success Rate**: 2/2 (100%)

## Usage Examples

### For Traditional Sportsbooks (DraftKings, FanDuel, Hard Rock Bet):
- "What's the spread on the Chiefs game?"
- "Compare the moneyline vs spread for the Patriots."
- "Which games have key number spreads (3 or 7)?"

### For DFS/Player Props (PrizePicks):
- Currently limited - The Odds API has player props but we'd need to expand the tool
- Add `markets=player_pass_tds,player_anytime_td` support

### For Strategy/Education:
- "Explain the Kelly Criterion."
- "Why is 3 such an important number?"
- "How should I size my bets with a $500 bankroll?"

## Next Steps for Production
1. ✅ **Model Selection**: granite4:3b configured
2. ✅ **Frontend**: Updated to default to granite4:3b
3. ⏳ **User Testing**: Test at https://bet.laserpointlabs.com with `das_service` account
4. 🔄 **Monitoring**: Track tool usage via logs to identify gaps

## Known Limitations
- **NCAA**: Only works during season (currently available)
- **Player Props**: Not yet implemented (could add to live_sports server)
- **Historical Data**: Not enabled (would need separate endpoint)
