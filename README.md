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
| Phase 1 | Core Game Engine | Not Started |
| Phase 2 | Probability Calculator | Not Started |
| Phase 3 | Agent Implementation | Not Started |
| Phase 4 | Simulation Framework | Not Started |
| Phase 5 | Analysis and Visualization | Not Started |

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/camelup.git
cd camelup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# Run simulation
python -m src.simulation.runner

# Run tests
pytest tests/
```

## License

MIT

## Author

David Luk
