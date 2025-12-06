# Comprehensive Betting Test Suite - NFL, NCAA, PrizePicks

## NFL TRADITIONAL SPORTSBOOK QUESTIONS
NFL_TRADITIONAL = [
    "What are the odds for the Chiefs game?",
    "Who is favored in the Saints game?",
    "What's the spread on the Bills vs Bengals game?",
    "Show me the over/under for the 49ers game?",
    "Should I bet Chiefs -3.5 or wait for the line to move?",
    "Compare DraftKings vs FanDuel lines for the Cowboys game.",
    "Which NFL game has the tightest spread this week?",
    "Are there any key number spreads (3 or 7) available Sunday?",
]

## NCAA FOOTBALL QUESTIONS
NCAA_TRADITIONAL = [
    "What are the odds for the Alabama game?",
    "Show me the spread for Georgia vs Tennessee.",
    "Who is favored in the Ohio State game?",
    "What's the total for the Michigan game?",
    "Should I bet on undefeated teams in cupcake games?",
    "How do recruiting rankings affect college football spreads?",
    "Alabama vs Georgia - which is better value, spread or moneyline?",
]

## PRIZEPICKS / DFS / PLAYER PROPS
PRIZEPICKS_QUESTIONS = [
    "What are Patrick Mahomes passing yards props?",
    "Show me Travis Kelce receiving yards on PrizePicks.",
    "What's the over/under for Derrick Henry rushing yards?",
    "Give me the top 3 QB passing props for Sunday.",
    "Should I take Jalen Hurts over or under on passing TDs?",
    "Build me a 3-leg PrizePicks parlay for NFL Sunday.",
    "What's the correlation between QB and WR props?",
    "Show me the highest value props for tonight's game.",
]

## PARLAY & TEASER QUESTIONS
PARLAY_QUESTIONS = [
    "I want to parlay Chiefs -3.5, Bills -5, 49ers -7. Is this smart?",
    "Explain the difference between a parlay and a teaser.",
    "What's a 6-point teaser and when should I use it?",
    "I hit 2/3 legs of my parlay. Should I hedge the last leg?",
    "Compare a 3-team parlay vs 3 straight bets - which is better?",
]

## STRATEGY & RISK MANAGEMENT (Cross-Sport)
STRATEGY_CROSS = [
    "I have $2000 bankroll for NFL and college. How should I allocate?",
    "Should I bet more on NFL or college football?",
    "What's riskier: spreads, totals, or player props?",
    "I'm up $500 this week. Should I increase my unit size?",
    "Explain how to use the Kelly Criterion for parlays.",
    "What's the optimal parlay size to maximize EV?",
    "Should I mix NFL and college in the same parlay?",
]

## SITUATIONAL / ADVANCED
ADVANCED_QUESTIONS = [
    "West Coast team traveling East for 1pm kickoff - bet against them?",
    "Thursday Night Football road favorite - fade or ride?",
    "College bowl game: motivated underdog vs unmotivated favorite?",
    "How do I evaluate a player prop with injury uncertainty?",
    "Rain in the forecast - bet under or avoid the game?",
    "Line moved from -3 to -3.5. Did I get good closing line value?",
]

ALL_QUESTIONS = (
    NFL_TRADITIONAL +
    NCAA_TRADITIONAL +
    PRIZEPICKS_QUESTIONS +
    PARLAY_QUESTIONS +
    STRATEGY_CROSS +
    ADVANCED_QUESTIONS
)

if __name__ == "__main__":
    print(f"Total Questions: {len(ALL_QUESTIONS)}")
    print(f"\nBy Category:")
    print(f"  NFL Traditional: {len(NFL_TRADITIONAL)}")
    print(f"  NCAA Traditional: {len(NCAA_TRADITIONAL)}")
    print(f"  PrizePicks/Props: {len(PRIZEPICKS_QUESTIONS)}")
    print(f"  Parlays/Teasers: {len(PARLAY_QUESTIONS)}")
    print(f"  Strategy/Risk: {len(STRATEGY_CROSS)}")
    print(f"  Advanced/Situational: {len(ADVANCED_QUESTIONS)}")
