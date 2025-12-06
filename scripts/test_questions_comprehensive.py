# Comprehensive Betting Test Questions
# Covers NFL, NCAA, Traditional Sportsbooks, and DFS (PrizePicks-style)

TRADITIONAL_SPORTSBOOK_QUESTIONS = [
    # Live Odds - NFL
    "What are the current odds for the Chiefs game?",
    "Who is favored in the Bills vs Dolphins game?",
    "What's the spread on the 49ers game?",
    "Show me the over/under for the Cowboys vs Eagles game.",
    "What are the moneyline odds for all Sunday afternoon games?",

    # Live Odds - NCAA
    "What are the odds for Alabama's next game?",
    "Show me the spread for the Ohio State vs Michigan game.",
    "What's the total for the Georgia game?",

    # Comparative Analysis
    "Which NFL game has the tightest spread this week?",
    "What's the biggest favorite in the NFL right now?",
    "Are there any NFL games with a key number spread (3 or 7)?",
    "Which bookmaker has the best line for the Ravens game?",

    # Timing & Line Movement
    "Should I bet on the Patriots now or wait closer to kickoff?",
    "Has the line moved on the Bengals game?",
]

STRATEGY_QUESTIONS = [
    # Bankroll Management
    "I have a $1000 bankroll. How much should I bet per game?",
    "What's the Kelly Criterion and should I use it?",
    "I'm down $200 this week. Should I increase my bet size to win it back?",
    "What's the difference between flat betting and variable betting?",

    # NFL Strategy
    "Why is 3 such an important number in NFL betting?",
    "Should I take the Packers at -2.5 or wait for -3?",
    "What's the value of home field advantage in the NFL?",
    "Is there an edge betting on West Coast teams traveling East for early games?",
    "Should I bet on Thursday Night Football road teams?",

    # NCAA Strategy
    "What's more important in college football betting: coaching or talent?",
    "How do I evaluate a bowl game matchup?",
    "Should I bet on undefeated teams against cupcake opponents?",
    "Do recruiting rankings predict college football performance?",

    # Risk Management
    "Should I parlay my NFL picks or bet them straight?",
    "What's a teaser and when should I use one?",
    "How do I hedge a future bet?",
    "Is it smart to bet the middle on a game?",
]

DFS_PRIZEPICKS_QUESTIONS = [
    # Player Props (Note: We may not have this data yet)
    "What are the player prop odds for Patrick Mahomes passing yards?",
    "Show me the over/under for Travis Kelce receiving yards.",
    "What are the rushing props for Derrick Henry?",
    "Which QB has the best passing yards over/under value today?",

    # DFS Strategy
    "How do I build a PrizePicks lineup?",
    "Should I take more overs or unders in DFS?",
    "What's the correlation between QB and WR props?",
    "Is it safer to bet on game totals or player props?",
]

CONTEXTUAL_QUESTIONS = [
    # Weather/Conditions
    "How does wind affect NFL totals?",
    "Should I bet the under if it's raining?",

    # Situational
    "What's a lookahead spot in NFL betting?",
    "Should I bet on a team coming off a bye week?",
    "Are division games harder to predict?",

    # Glossary
    "What does 'closing line value' mean?",
    "What's the difference between sharp money and square money?",
    "What does 'steam move' mean?",
    "Explain what 'buying points' means.",
]

MULTI_PART_QUESTIONS = [
    "I want to bet on the Chiefs -7. Explain the risks and suggest a bet size for a $500 bankroll.",
    "Compare the Saints spread vs their moneyline. Which is better value?",
    "I'm building a 3-team parlay with the Bills, 49ers, and Eagles. What do you think?",
    "Should I take Alabama -14.5 or the under 56.5 in their game?",
]

ALL_QUESTIONS = (
    TRADITIONAL_SPORTSBOOK_QUESTIONS +
    STRATEGY_QUESTIONS +
    DFS_PRIZEPICKS_QUESTIONS +
    CONTEXTUAL_QUESTIONS +
    MULTI_PART_QUESTIONS
)

if __name__ == "__main__":
    print(f"Generated {len(ALL_QUESTIONS)} test questions")
    print("\nCategories:")
    print(f"  - Traditional Sportsbook: {len(TRADITIONAL_SPORTSBOOK_QUESTIONS)}")
    print(f"  - Strategy: {len(STRATEGY_QUESTIONS)}")
    print(f"  - DFS/PrizePicks: {len(DFS_PRIZEPICKS_QUESTIONS)}")
    print(f"  - Contextual: {len(CONTEXTUAL_QUESTIONS)}")
    print(f"  - Multi-part: {len(MULTI_PART_QUESTIONS)}")
