# Monte Carlo Analysis of Skill vs. Luck in Camel Up

A data science project that quantifies the role of skill versus luck in the board game [Camel Up](https://boardgamegeek.com/boardgame/153938/camel) through Monte Carlo simulation.

## Research Questions

1. What is the win rate of EV-optimal play vs. random play?
2. What is the coefficient of variation (CV) of final scores?
3. What is the mean score advantage of optimal play per game?
4. How do these metrics compare to known skill-based and luck-based games?

## Motivation

Camel Up is a popular betting game where players wager on camel races. Despite using probability calculations to make optimal bets, skilled players often lose due to high variance from the camel stacking mechanic. This project investigates whether the game is predominantly luck-based by simulating thousands of games.

## Key Findings

| Matchup | Win Rate | 95% CI | Score Advantage |
|---------|----------|--------|-----------------|
| Greedy vs Random | **99.8%** | [0.995, 1.000] | +61.1 coins |
| Heuristic vs Random | 98.5% | [0.977, 0.993] | +45.4 coins |
| Conservative vs Random | 98.1% | [0.973, 0.989] | +52.0 coins |
| Greedy vs Heuristic | 86.3% | [0.841, 0.884] | +11.5 coins |
| Greedy vs Conservative | 74.1% | [0.714, 0.769] | +7.9 coins |
| Greedy vs Greedy | 51.2% | [0.481, 0.544] | +0.3 coins |

**Conclusion**: Camel Up has an extremely high skill ceiling. EV-optimal play
wins 99.8% against random -- exceeding even Chess on the reference spectrum.
However, when two equally skilled players meet, dice dominate and the outcome
reverts to a coin flip (51.2%). The "skill" is knowing *when* and *what* to
bet, not deep strategic interaction.

**Limitations**: Results use fast_mode=True (grey die excluded from probability
calculations, 29K outcomes instead of 1M). 1,000 games per matchup. See
[SIMULATION_GUIDE.md](SIMULATION_GUIDE.md) for details.

## Methodology

- **Monte Carlo Simulation**: 1,000 games per matchup, 7 matchups, seat alternation to eliminate first-player bias
- **Agent-Based Modeling**: Random, Greedy (EV-optimal), Heuristic (rule-based), and Conservative (risk-averse) strategies
- **Statistical Analysis**: Win rates with 95% Wald CI, paired t-test, coefficient of variation

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for detailed methodology and [SIMULATION_GUIDE.md](SIMULATION_GUIDE.md) for how to run and interpret simulations.

## Skill Spectrum

| Game | Optimal vs Random Win Rate | Skill Level |
|------|---------------------------|-------------|
| Roulette | ~47% | Pure luck |
| Blackjack | ~49% | Low skill |
| Poker (heads-up) | ~55-60% | Moderate skill |
| Backgammon | ~65-75% | Moderate-high skill |
| Chess | ~95%+ | Pure skill |
| **Camel Up** | **99.8%** | **Extreme skill ceiling** |

## Project Status

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Core Game Engine | Complete (135 tests) |
| Phase 2 | Probability Calculator | Complete (25 tests) |
| Phase 3 | Agent Implementation | Complete (23 tests) |
| Pre-Phase 4 | Monte Carlo Validation | Complete (10 tests) |
| Phase 4 | Simulation Framework | Complete (33 tests, results collected) |
| Phase 5 | Analysis and Visualization | Not Started |

**Total: 239 tests (236 non-slow)**

## Installation

```bash
git clone https://github.com/davcwluk/camelup-monte-carlo.git
cd camelup-monte-carlo

# Install PyPy (6-10x faster than CPython)
brew install pypy3  # Mac
# or download from https://www.pypy.org/download.html (Windows)

pypy3 -m pip install pytest pytest-xdist
```

## Usage

```bash
# Run all tests in parallel across all CPU cores
pypy3 -m pytest tests/ -v -n auto

# Skip slow tests (grey die enumeration ~1M outcomes)
pypy3 -m pytest tests/ -v -n auto -m "not slow"

# Run the full simulation (7 matchups x 1000 games)
pypy3 run_simulation.py
```

Results are saved to `results/*.csv`. See [SIMULATION_GUIDE.md](SIMULATION_GUIDE.md) for detailed instructions.

## Performance

The probability calculator enumerates all possible dice outcomes:
- **fast_mode=True** (no grey die): 29,160 outcomes per decision
- **fast_mode=False** (with grey die): ~1,000,000 outcomes per decision

| Runtime | 1000 Games (12 CPU cores) |
|---------|---------------------------|
| PyPy + fast_mode | ~20 minutes |
| PyPy + full mode | ~3.5 hours |

Test execution (validation suite, 8 tests including slow):

| Configuration | Wall Time | Speedup |
|---------------|-----------|---------|
| CPython, single-core | 232s | 1x |
| PyPy, single-core | 24s | 9.7x |
| PyPy + pytest-xdist, 12 cores | 13s | 17.8x |

## License

MIT

## Author

David Luk
