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
- **5 Racing Dice**: Each shows 1, 1, 2, 2, 3, 3 (6 faces, each value has 1/3 probability)
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

### 6. BoundedGreedyAgent
- **Logic**: GreedyAgent with depth-limited probability calculation
  - Only enumerates next `depth_limit` dice outcomes (default 2)
  - 180 outcomes at depth=2 vs 29,160 for full enumeration
- **Purpose**: Model human cognitive limits ("bounded rationality")

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

### Phase 1: Core Game Engine [COMPLETE]
- [x] Implement game board and track representation
- [x] Implement camel and stack mechanics
- [x] Implement dice and pyramid mechanics
- [x] Implement betting ticket system
- [x] Implement spectator tile mechanics
- [x] Implement leg scoring
- [x] Implement game end detection and final scoring
- [x] Unit tests for all game mechanics (135 tests passing)

### Phase 2: Probability Calculator [COMPLETE]
- [x] Enumerate all possible leg outcomes (this IS the probability calculation)
- [x] Calculate camel ranking probabilities: P(camel finishes 1st/2nd/etc)
- [x] Calculate EV for leg betting tickets
- [x] Calculate EV for pyramid ticket (+1 coin guaranteed)
- [x] Performance: 5 racing dice in 0.45s, with grey die ~29s
- [x] Calculate EV for spectator tile placement
- [x] Calculate EV for overall winner/loser bets

### Phase 3: Agent Implementation [COMPLETE]
- [x] Implement base Agent interface
- [x] Implement RandomAgent
- [x] Implement GreedyAgent (with overall bet threshold)
- [x] Implement HeuristicAgent
- [x] Implement ConservativeAgent
- [ ] OptimalAgent (deferred - GreedyAgent provides sufficient EV optimization)

### Pre-Phase 4: Validation and Performance [COMPLETE]
- [x] Monte Carlo validation tests (8 tests verifying calculator against independent simulations)
- [x] PyPy + pytest-xdist parallel test execution setup (~18x speedup over CPython single-core)
- [x] Human-readable game logger for debugging (GameLogger, renderers, play_game integration)

### Phase 4: Simulation Framework [COMPLETE]
- [x] SimulationRunner with serial and parallel execution (multiprocessing)
- [x] Agent registry, GameConfig, module-level worker for pickling
- [x] GameResult/MatchupResult frozen dataclasses with CSV I/O
- [x] Analysis module: win rate, CI, t-test, CV, summary_text (stdlib only)
- [x] Alternating start player (even game_index: A first; odd: B first)
- [x] First-player win rate as separate bias metric
- [x] Progress tracking with flush for background runs
- [x] Production results: 7 matchups x 1,000 games (fast_mode=True)
- [x] Simulation guide document (SIMULATION_GUIDE.md)
- [x] BoundedGreedyAgent: depth-limited GreedyAgent (default depth=2, 180 outcomes)
- [x] N-player simulation: NPlayerRunner, NPlayerMatchupResult, focal-vs-field analysis
- [x] N-player seat rotation (game i -> focal in seat i % N)
- [x] N-player CSV I/O with dynamic columns (auto-detects N on load)
- [x] Production N-player results: 9 matchups x 1,000 games (2P/4P/6P, Greedy/BoundedGreedy vs Random/Heuristic)
- [x] Multi-player scaling experiments confirming skill does NOT decay toward 1/N

### Phase 5: Analysis and Visualization
- [ ] Win rate calculations and confidence intervals
- [ ] Score distribution histograms
- [ ] Variance analysis
- [ ] EV accuracy scatter plots
- [ ] Statistical significance tests
- [ ] Comparison charts against reference games
- [ ] Rename "OptimalAgent" to "ProbabilisticAgent" in analysis output
- [ ] Track Sharpe Ratio equivalent metric (Mean Excess Return / Std Dev)
- [ ] Parameter sensitivity analysis for HeuristicAgent thresholds
- [ ] Implement GameAwareGreedyAgent (score differential utility)
- [x] Multi-player scaling experiments (4, 6 players) for Skill Decay Curve

---

## Technical Decisions

### Language
Python (for data analysis libraries and rapid prototyping)

### Runtime
- **PyPy 3.10**: 6-10x faster than CPython for probability calculations
- Install: `brew install pypy3` (Mac) or download from pypy.org (Windows)
- Run: `pypy3 -m pytest tests/` or `pypy3 script.py`

### Key Libraries
- `numpy`: Numerical computations
- `pandas`: Data analysis and results storage
- `matplotlib`/`seaborn`: Visualization
- `scipy`: Statistical tests
- `pytest`: Unit testing
- `pytest-xdist`: Parallel test execution across CPU cores (`-n auto`)
- `multiprocessing`: Parallel game simulation

### Performance Benchmarks

| Mode | Outcomes/Decision | 1000 Games (PyPy + 12 cores) |
|------|-------------------|------------------------------|
| fast_mode=True (no grey die) | 29,160 | ~20 minutes |
| fast_mode=False (with grey die) | ~1,000,000 | ~3.5 hours |

Single decision timing (PyPy vs Python):
- fast_mode=True: PyPy 0.35s vs Python 1.45s (4x faster)
- fast_mode=False: PyPy 8.3s vs Python 79s (9.5x faster)

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
│   │   ├── calculator.py     # Exact probability enumeration (29K-1M outcomes)
│   │   └── ev.py             # Expected value calculations for betting
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py           # Base agent interface
│   │   ├── random_agent.py
│   │   ├── greedy_agent.py
│   │   ├── heuristic_agent.py
│   │   ├── optimal_agent.py
│   │   ├── bounded_greedy_agent.py
│   │   └── conservative_agent.py
│   ├── logging/
│   │   ├── __init__.py
│   │   ├── renderer.py       # Board/state text rendering
│   │   └── game_logger.py    # Per-game human-readable logger
│   └── simulation/
│       ├── __init__.py
│       ├── results.py        # GameResult, MatchupResult, CSV I/O
│       ├── runner.py         # SimulationRunner, agent registry, worker
│       ├── analysis.py       # Win rate, CI, t-test, CV, summary
│       ├── n_player_results.py  # NPlayerMatchupResult, CSV I/O
│       ├── n_player_runner.py   # NPlayerRunner, seat rotation
│       └── n_player_analysis.py # Focal-vs-field analysis
├── tests/
│   ├── __init__.py
│   ├── test_dice.py           # 12 tests - dice and pyramid mechanics
│   ├── test_camel.py          # 28 tests - camel and stack mechanics
│   ├── test_game.py           # 9 tests - game state and actions
│   ├── test_betting.py        # 30 tests - betting tickets and scoring
│   ├── test_spectator.py      # 17 tests - spectator tile mechanics
│   ├── test_movement.py       # 20 tests - movement and board integration
│   ├── test_game_flow.py      # 19 tests - turns, legs, game end
│   ├── test_probability.py    # 25 tests - probability and EV calculations
│   ├── test_agents.py         # 23 tests - agent implementations (1 marked slow)
│   ├── test_probability_validation.py  # 10 tests - Monte Carlo validation (2 marked slow)
│   ├── test_game_logger.py    # 13 tests - renderer + logger integration
│   ├── test_simulation.py     # 33 tests - simulation framework
│   └── test_n_player_simulation.py  # 30 tests - N-player simulation
├── notebooks/
│   └── analysis.ipynb        # Results visualization
└── results/
    └── .gitkeep
```

---

## Simulation Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Number of players | 2, 4, 6 | 2P for paired analysis, 4P/6P for skill decay experiments |
| Games per matchup | Adaptive N (start 1,000; scale up if 95% CI > +/-1%) | See question.md Q4 |
| Random seed | Fixed for reproducibility | Reproducibility |
| Track length | 16 spaces (standard) | Per rulebook |

### Matchups to Run
1. RandomAgent vs RandomAgent (baseline variance) [DONE]
2. GreedyAgent vs RandomAgent (primary skill test) [DONE]
3. HeuristicAgent vs RandomAgent (human-like test) [DONE]
4. ConservativeAgent vs RandomAgent (risk-averse test) [DONE]
5. GreedyAgent vs HeuristicAgent (strategy comparison) [DONE]
6. GreedyAgent vs ConservativeAgent (strategy comparison) [DONE]
7. GreedyAgent vs GreedyAgent (skill equilibrium) [DONE]

Note: OptimalAgent was deferred -- GreedyAgent serves as the EV-optimal agent.

---

## Analysis Plan

### RQ1: Win Rate of Optimal vs Random
- Run adaptive N games of OptimalAgent vs RandomAgent (start 1,000; scale up if 95% CI > +/-1%)
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
| Phase 1 | Core Game Engine | Complete (135 tests) |
| Phase 2 | Probability Calculator | Complete (25 tests) |
| Phase 3 | Agent Implementation | Complete (23 tests) |
| Pre-Phase 4 | Validation and Performance | Complete (8 tests) |
| Phase 4 | Simulation Framework | Complete (63 tests, 7 two-player + 9 N-player matchups run) |
| Phase 5 | Analysis and Visualization | Not Started |

**Total: 281 tests (3 marked slow)**

---

## References

- Camel Up Rulebook (2nd Edition, 2018)
- [Camel Up Calculator - GitHub](https://github.com/cbhua/camel-up-calculator)
- [Camel Up Probability Calculator](https://karoletrych.github.io/camel-up-probability/)
- [Analysis of Probabilities in Camel Up - BoardGameGeek](https://boardgamegeek.com/thread/1400375/analysis-of-probabilities-in-camel-cup)
