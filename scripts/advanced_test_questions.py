# ADVANCED & REALISTIC GAMBLER TEST SUITE

# ------------------------------------------------------------------------------
# 1. SHARP / PROFESSIONAL BETTING (Line Shopping & Value)
# ------------------------------------------------------------------------------
SHARP_QUESTIONS = [
    "Compare the implied probability of the Chiefs -200 moneyline vs their -3.5 spread at -110.",
    "I see the Bills line moved from -2.5 to -3. Is this 'steam' or just public money? Should I still bet it?",
    "Which sportsbook has the best price for the 49ers moneyline right now: DraftKings or FanDuel?",
    "Calculate the hold percentage for the Eagles/Cowboys moneyline market.",
    "Is there any Closing Line Value (CLV) value in taking the Ravens at +3 (-120) if the market consensus is +2.5?",
    "Find me a middle opportunity for the Bengals game. Is there a gap between books?",
]

# ------------------------------------------------------------------------------
# 2. PLAYER PROPS & DFS (PrizePicks / Underdog Focus)
# ------------------------------------------------------------------------------
PRIZEPICKS_ADVANCED = [
    "Analyze the correlation between Patrick Mahomes passing yards and Travis Kelce receiving yards. Should I stack the Over on both?",
    "I need a 'safe' floor play for a PrizePicks 2-man power play. Who is the most consistent RB1 this week?",
    "Compare Lamar Jackson's rushing yards prop on PrizePicks vs the line on DraftKings. Is there an edge?",
    "What is the hit rate for Derrick Henry's rushing over in the last 5 games?",
    "Evaluate a 'Same Game Parlay' approach: If I bet the Over 54.5 in the Dolphins game, which WR props correlate best?",
    "Are kicker props (Field Goals Made) impacted by the 15mph wind forecast in Buffalo?",
]

# ------------------------------------------------------------------------------
# 3. SITUATIONAL & HANDICAPPING ANGLES
# ------------------------------------------------------------------------------
SITUATIONAL_QUESTIONS = [
    "The Saints are playing on short rest (Thursday) after an overtime game. Historically, how do road teams perform in this spot?",
    "Fade the public: Which NFL game has the highest percentage of public bets but the line is moving the OTHER way (Reverse Line Movement)?",
    "How does the injury to the Eagles' starting Left Tackle impact their run game projection against a top-5 D-line?",
    "Alabama is a 28-point favorite. Do Nick Saban (or current coach) teams typically cover big spreads in non-conference games?",
    "Is there a 'letdown spot' for Georgia after beating their rival last week? Should I bet the first half underdog?",
]

# ------------------------------------------------------------------------------
# 4. LIVE / IN-GAME BETTING (Micro-Moments)
# ------------------------------------------------------------------------------
LIVE_BETTING = [
    "The Chiefs are down 14-0 in the first quarter. What is their new live moneyline, and is it a good hedge opportunity?",
    "The total was 45.5 pre-game. It's 0-0 at halftime. Should I smash the live Under or is regression coming?",
    "Can I hedge my pre-game parlay (last leg pending) with a live bet on the opponent? Calculate the hedge amount to lock in profit.",
]

# ------------------------------------------------------------------------------
# 5. BANKROLL & RISK (Advanced)
# ------------------------------------------------------------------------------
RISK_MANAGEMENT = [
    "I have a $5,000 bankroll. I want to place a 3-unit bet on a 5-leg parlay. Talk me out of it using Expected Value (EV) math.",
    "Explain why buying the half-point from -3.5 to -3 is expensive math-wise. What is the break-even win percentage needed?",
    "If I use the Quarter-Kelly criterion for a bet with a 5% estimated edge, what is my exact wager amount?",
]

ALL_ADVANCED_QUESTIONS = (
    SHARP_QUESTIONS +
    PRIZEPICKS_ADVANCED +
    SITUATIONAL_QUESTIONS +
    LIVE_BETTING +
    RISK_MANAGEMENT
)
