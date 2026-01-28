# Monte Carlo Analysis of Skill vs. Luck in Camel Up

## Project Goal

Quantify the role of skill versus luck in the board game Camel Up by simulating thousands of games with different agent strategies. This project answers the question: **Does probability-optimal play provide a meaningful advantage over random play?**

---

## Research Questions

| ID | Question |
|----|----------|
| RQ1 | What is the win rate of EV-optimal play vs. random play? |
| RQ2 | What is the coefficient of variation (CV) of final scores? |
| RQ3 | What is the mean score advantage of optimal play per game? |
| RQ4 | How do these metrics compare to known skill-based and luck-based games? |

### Context for Interpretation

To interpret results, we compare against known reference points:

| Game | Skill Level | Optimal vs Random Win Rate | Notes |
|------|-------------|---------------------------|-------|
| Roulette | Pure luck | ~47% (house edge) | No decision affects outcome |
| Blackjack | Low skill | ~49% (basic strategy) | Optimal play reduces house edge |
| Poker (heads-up) | Moderate skill | ~55-60% | Pros vs amateurs, short-term |
| Backgammon | Moderate-high skill | ~65-75% | Dice + strategy |
| Chess | Pure skill | ~95%+ | Masters vs beginners |

**If Camel Up optimal play wins ~50-55%**, it suggests the game is predominantly luck-based.
**If Camel Up optimal play wins ~60-70%**, it suggests meaningful skill expression.

---

## Game Mechanics Summary

### Components
- **5 Racing Camels**: Blue, Green, Yellow, Red, Purple (move clockwise)
- **2 Crazy Camels**: Black, White (move counter-clockwise, carry camels backwards)
- **5 Racing Dice**: Each shows 1, 2, 2, 3, 3 (not uniform distribution)
- **1 Grey Die**: Controls crazy camels (1, 2, 3 in white; 1, 2, 3 in black)
- **16 Spaces**: Racing track with finish line

### Key Mechanics
1. **Camel Stacking**: Camels on same space form stacks; moving camel carries all camels above it
2. **Legs**: A leg ends when 5 of 6 dice have been revealed
3. **Betting Tickets**: Available in 5, 3, 2, 2 coin values per camel color
4. **Spectator Tiles**: Modify movement by +1 or -1 when camels land on them
5. **Overall Winner/Loser Bets**: Secret bets on final race outcome

### Scoring (Per Leg)
- Bet on 1st place camel: +5/+3/+2/+2 (depending on ticket taken)
- Bet on 2nd place camel: +1
- Bet on any other camel: -1
- Pyramid ticket: +1 per ticket

### Scoring (End of Game)
- Correct overall winner/loser (1st to bet): +8
- Correct overall winner/loser (2nd to bet): +5
- Correct overall winner/loser (3rd to bet): +3
- Correct overall winner/loser (4th to bet): +2
- Correct overall winner/loser (5th+ to bet): +1
- Incorrect overall bet: -1

---

## Agent Strategies

### 1. RandomAgent
- **Logic**: Uniformly random selection from all legal actions
- **Purpose**: Baseline for comparison

### 2. GreedyAgent
- **Logic**: Always takes the highest immediate expected value action
- **Calculation**: For each legal action, compute immediate EV and pick maximum
- **Purpose**: Simple EV-based strategy

### 3. HeuristicAgent
- **Logic**: Rule-based human-like strategy
  - If leader has > 40% win probability, take their betting ticket
  - If all tickets for likely winners taken, roll dice
  - Place spectator tile if early in leg and good position available
- **Purpose**: Approximate casual human play

### 4. OptimalAgent
- **Logic**: Full probability tree calculation
  - Enumerate all possible remaining dice outcomes
  - Calculate exact win probability for each camel
  - Choose action maximizing expected final score
- **Purpose**: Theoretical optimal play (computationally expensive)

### 5. ConservativeAgent
- **Logic**: Risk-averse strategy
  - Only bet when probability > 50%
  - Prefer pyramid tickets for guaranteed +1
  - Avoid overall winner/loser bets unless very confident
- **Purpose**: Test low-variance strategy

---

## Metrics to Track

### Primary Metrics
| Metric | Description | Unit |
|--------|-------------|------|
| Win Rate | % of games won by each agent type | % |
| Mean Final Score | Average coins at game end | Coins |
| Score Std Dev | Standard deviation of final scores | Coins |
| Coefficient of Variation | Std Dev / Mean (normalized variance) | Ratio |
| Score Differential | Winner score minus loser score | Coins |

### Secondary Metrics
| Metric | Description | Unit |
|--------|-------------|------|
| EV Accuracy | Correlation between predicted EV and actual return | r |
| Decision Impact | % of decisions where best/worst action differ by > 1 EV | % |
| Leg Win Rate | % of legs where optimal bettor wins | % |
| Comeback Frequency | % of games where leader after leg 1 loses | % |

---

## Implementation Plan

### Phase 1: Core Game Engine
- [ ] Implement game board and track representation
- [ ] Implement camel and stack mechanics
- [ ] Implement dice and pyramid mechanics
- [ ] Implement betting ticket system
- [ ] Implement spectator tile mechanics
- [ ] Implement leg scoring
- [ ] Implement game end detection and final scoring
- [ ] Unit tests for all game mechanics

### Phase 2: Probability Calculator
- [ ] Calculate remaining dice probabilities
- [ ] Enumerate all possible leg outcomes
- [ ] Calculate camel position probabilities
- [ ] Calculate expected value for each betting ticket
- [ ] Optimize for performance (memoization, pruning)

### Phase 3: Agent Implementation
- [ ] Implement base Agent interface
- [ ] Implement RandomAgent
- [ ] Implement GreedyAgent
- [ ] Implement HeuristicAgent
- [ ] Implement OptimalAgent
- [ ] Implement ConservativeAgent

### Phase 4: Simulation Framework
- [ ] Game loop with multiple agents
- [ ] Batch simulation runner
- [ ] Results logging and storage
- [ ] Progress tracking for long runs

### Phase 5: Analysis and Visualization
- [ ] Win rate calculations and confidence intervals
- [ ] Score distribution histograms
- [ ] Variance analysis
- [ ] EV accuracy scatter plots
- [ ] Statistical significance tests
- [ ] Comparison charts against reference games

---

## Technical Decisions

### Language
Python (for data analysis libraries and rapid prototyping)

### Key Libraries
- `numpy`: Numerical computations
- `pandas`: Data analysis and results storage
- `matplotlib`/`seaborn`: Visualization
- `scipy`: Statistical tests
- `pytest`: Unit testing

### Project Structure
```
camelup/
├── PROJECT_PLAN.md
├── README.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── game/
│   │   ├── __init__.py
│   │   ├── board.py          # Board and track representation
│   │   ├── camel.py          # Camel and stack mechanics
│   │   ├── dice.py           # Dice and pyramid mechanics
│   │   ├── betting.py        # Betting tickets and scoring
│   │   ├── spectator.py      # Spectator tile mechanics
│   │   └── game.py           # Main game loop
│   ├── probability/
│   │   ├── __init__.py
│   │   ├── calculator.py     # Probability calculations
│   │   └── ev.py             # Expected value calculations
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py           # Base agent interface
│   │   ├── random_agent.py
│   │   ├── greedy_agent.py
│   │   ├── heuristic_agent.py
│   │   ├── optimal_agent.py
│   │   └── conservative_agent.py
│   └── simulation/
│       ├── __init__.py
│       ├── runner.py         # Simulation runner
│       └── analysis.py       # Results analysis
├── tests/
│   ├── __init__.py
│   ├── test_board.py
│   ├── test_camel.py
│   ├── test_dice.py
│   ├── test_betting.py
│   ├── test_probability.py
│   └── test_agents.py
├── notebooks/
│   └── analysis.ipynb        # Results visualization
└── results/
    └── .gitkeep
```

---

## Simulation Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Number of players | 2 | Simplifies analysis, clearer skill signal |
| Games per matchup | 10,000 | Statistical significance |
| Random seed | Fixed for reproducibility | Reproducibility |
| Track length | 16 spaces (standard) | Per rulebook |

### Matchups to Run
1. RandomAgent vs RandomAgent (baseline variance)
2. OptimalAgent vs RandomAgent (skill test - primary)
3. GreedyAgent vs RandomAgent (simple EV test)
4. HeuristicAgent vs RandomAgent (human-like test)
5. OptimalAgent vs OptimalAgent (optimal equilibrium)
6. OptimalAgent vs GreedyAgent (strategy comparison)

---

## Analysis Plan

### RQ1: Win Rate of Optimal vs Random
- Run 10,000 games of OptimalAgent vs RandomAgent
- Calculate win rate with 95% confidence interval
- Compare to reference games (see Context for Interpretation)

### RQ2: Coefficient of Variation
- Calculate CV = σ / μ for final scores across all matchups
- Higher CV indicates more variance/luck influence
- Compare RandomAgent vs RandomAgent CV to OptimalAgent vs RandomAgent CV

### RQ3: Mean Score Advantage
- Calculate mean(OptimalAgent score) - mean(RandomAgent score) per game
- Express as both absolute coins and percentage of mean score
- Calculate statistical significance (t-test)

### RQ4: Comparison to Reference Games
- Plot Camel Up metrics alongside known games
- Create "skill spectrum" visualization
- Discuss where Camel Up falls on the luck-skill continuum

---

## Timeline

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Core Game Engine | Not Started |
| Phase 2 | Probability Calculator | Not Started |
| Phase 3 | Agent Implementation | Not Started |
| Phase 4 | Simulation Framework | Not Started |
| Phase 5 | Analysis and Visualization | Not Started |

---

## References

- Camel Up Rulebook (2nd Edition, 2018)
- [Camel Up Calculator - GitHub](https://github.com/cbhua/camel-up-calculator)
- [Camel Up Probability Calculator](https://karoletrych.github.io/camel-up-probability/)
- [Analysis of Probabilities in Camel Up - BoardGameGeek](https://boardgamegeek.com/thread/1400375/analysis-of-probabilities-in-camel-cup)
