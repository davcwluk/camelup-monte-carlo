# Monte Carlo Analysis of Skill vs. Luck in Camel Up

A data science project that quantifies the role of skill versus luck in the board game [Camel Up](https://boardgamegeek.com/boardgame/153938/camel) through Monte Carlo simulation.

## Research Questions

1. What is the win rate of EV-optimal play vs. random play?
2. What is the coefficient of variation (CV) of final scores?
3. What is the mean score advantage of optimal play per game?
4. How do these metrics compare to known skill-based and luck-based games?

## Motivation

Camel Up is a popular betting game where players wager on camel races. Despite using probability calculations to make optimal bets, skilled players often lose due to high variance from the camel stacking mechanic. This project investigates whether the game is predominantly luck-based by simulating thousands of games.

## Methodology

- **Monte Carlo Simulation**: 10,000+ games per agent matchup
- **Agent-Based Modeling**: Random, Greedy, Heuristic, and Optimal strategies
- **Statistical Analysis**: Win rates, score variance, and EV accuracy

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for detailed methodology and implementation plan.

## Context for Interpretation

| Game | Optimal vs Random Win Rate | Skill Level |
|------|---------------------------|-------------|
| Roulette | ~47% | Pure luck |
| Blackjack | ~49% | Low skill |
| Poker (heads-up) | ~55-60% | Moderate skill |
| Backgammon | ~65-75% | Moderate-high skill |
| Chess | ~95%+ | Pure skill |

## Project Status

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Core Game Engine | Complete (133 tests) |
| Phase 2 | Probability Calculator | Complete (25 tests) |
| Phase 3 | Agent Implementation | Complete (22 tests) |
| Phase 4 | Simulation Framework | Not Started |
| Phase 5 | Analysis and Visualization | Not Started |

## Installation

```bash
git clone https://github.com/davcwluk/camelup-monte-carlo.git
cd camelup-monte-carlo
pip install -r requirements.txt

# For faster execution (recommended):
brew install pypy3  # Mac
# or download from https://www.pypy.org/download.html (Windows)
```

## Usage

```bash
# Run tests (PyPy recommended for speed)
pypy3 -m pytest tests/

# Or with standard Python
python -m pytest tests/
```

## Performance

The probability calculator enumerates all possible dice outcomes:
- **fast_mode=True** (no grey die): 29,160 outcomes per decision
- **fast_mode=False** (with grey die): ~1,000,000 outcomes per decision

| Runtime | 1000 Games (12 CPU cores) |
|---------|---------------------------|
| Python + fast_mode | ~3 hours |
| PyPy + fast_mode | ~20 minutes |
| PyPy + full mode | ~3.5 hours |

## License

MIT

## Author

David Luk
