# End-to-End Simulation Guide

How to run production simulations, verify results, and interpret the output.

---

## Table of Contents

1. [Background](#1-background)
2. [Goal](#2-goal)
3. [Prerequisites](#3-prerequisites)
4. [Architecture Overview](#4-architecture-overview)
5. [Running Simulations](#5-running-simulations)
6. [Understanding the Output](#6-understanding-the-output)
7. [Verifying Results](#7-verifying-results)
8. [Expected Results](#8-expected-results)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Background

### What is Camel Up?

Camel Up is a betting board game where 5 racing camels (plus 2 "crazy" camels
that move backward) race around a 16-space track. Players do not control
camels directly. Instead, on each turn a player picks one action:

- **Take a leg betting ticket** -- bet on which camel will lead at the end of
  the current "leg" (a leg ends after 5 of 6 dice are rolled).
- **Take a pyramid ticket** -- roll a die to advance a random camel and earn a
  guaranteed +1 coin.
- **Place a spectator tile** -- put a +1 or -1 modifier on a track space. If
  any camel lands there, its movement is modified and the tile owner gets +1
  coin.
- **Bet on overall winner/loser** -- secret bet on which camel will finish
  first or last in the entire race.

The game ends when any camel crosses space 16. The player with the most coins
wins.

### What is this project?

This project is a Monte Carlo simulation that plays thousands of automated
Camel Up games between different AI agents to answer one question:

**Does probability-optimal play provide a meaningful advantage over random play?**

If an agent that calculates exact probabilities and picks the highest expected
value (EV) action only wins slightly more than 50% of the time against a random
player, then Camel Up is predominantly luck. If it wins 60--70%, there is
meaningful skill.

### What are the agents?

| Agent | Strategy | Speed |
|-------|----------|-------|
| `RandomAgent` | Picks a uniformly random legal action each turn | Instant |
| `GreedyAgent` | Enumerates all possible dice outcomes, calculates EV for every legal action, picks the highest | ~0.35s/turn (fast), ~8s/turn (full) |
| `BoundedGreedyAgent` | GreedyAgent with depth-limited enumeration (default depth=2, 180 outcomes). Models human cognitive limits | Fast |
| `HeuristicAgent` | Rule-based: bet on leader if P(1st) > 40%, place tiles early, roll when unsure | Medium |
| `ConservativeAgent` | Risk-averse: only bets when P > 50%, prefers guaranteed +1 pyramid tickets, never places tiles | Medium |

`GreedyAgent` has two modes:

- **fast_mode=True**: Skips the grey die (crazy camels). Enumerates 29,160
  outcomes per decision. Good for testing and quick runs.
- **fast_mode=False**: Includes the grey die. Enumerates ~1,000,000 outcomes
  per decision. This is the production mode for accurate results.

### Research questions

| ID | Question | Metric |
|----|----------|--------|
| RQ1 | What is the win rate of EV-optimal play vs random play? | Win rate with 95% CI |
| RQ2 | What is the coefficient of variation (CV) of final scores? | CV = std / mean |
| RQ3 | What is the mean score advantage of optimal play per game? | Mean difference in coins |
| RQ4 | How does Camel Up compare to known skill/luck games? | Position on spectrum |

### Reference points for interpretation

| Game | Skill level | Optimal vs random win rate |
|------|-------------|---------------------------|
| Roulette | Pure luck | ~47% |
| Blackjack | Low skill | ~49% |
| Poker (heads-up) | Moderate skill | ~55--60% |
| Backgammon | Moderate-high skill | ~65--75% |
| Chess | Pure skill | ~95%+ |

---

## 2. Goal

Run the following matchups and collect enough data to answer all four research
questions with statistical confidence:

| # | Matchup | Purpose |
|---|---------|---------|
| 1 | RandomAgent vs RandomAgent | Baseline: pure-luck variance |
| 2 | GreedyAgent vs RandomAgent | Primary skill test |
| 3 | HeuristicAgent vs RandomAgent | Human-like skill test |
| 4 | ConservativeAgent vs RandomAgent | Risk-averse skill test |
| 5 | GreedyAgent vs HeuristicAgent | Strategy comparison |
| 6 | GreedyAgent vs ConservativeAgent | Strategy comparison |
| 7 | GreedyAgent vs GreedyAgent | Mirror: skill equilibrium |

Each matchup should run at least 1,000 games. If the 95% confidence interval
on win rate is wider than +/-2%, scale up to 2,000--5,000 games.

---

## 3. Prerequisites

### Software

```
pypy3          # PyPy 3.10+ (6--10x faster than CPython)
pytest         # Test runner
pytest-xdist   # Parallel test execution
```

Install on macOS:
```bash
brew install pypy3
pypy3 -m pip install pytest pytest-xdist
```

### Verify the codebase

Before running any production simulation, confirm that all tests pass:

```bash
pypy3 -m pytest tests/ -v -n auto -m "not slow"
```

Expected output: **236 passed** (239 total collected, 3 slow tests skipped).

If any test fails, do not proceed. The probability calculator has been validated
against independent Monte Carlo simulations (`test_probability_validation.py`).
If those tests fail, all EV calculations are unreliable and simulation results
would be meaningless.

---

## 4. Architecture Overview

### Data flow

```
SimulationRunner
  |
  |-- creates GameConfig for each game
  |     (game_index, seed, agent names, fast_mode)
  |
  |-- dispatches to _run_single_game() [serial or multiprocessing pool]
  |     |
  |     |-- constructs agents from AGENT_REGISTRY (avoids pickling)
  |     |-- calls play_game(num_players=2, agents, seed)
  |     |-- returns GameResult
  |
  |-- collects all GameResult objects, sorts by game_index
  |-- returns MatchupResult
        |
        |-- save_results_csv() -> .csv file
        |-- analysis functions -> statistics
        |-- summary_text() -> human-readable report
```

### Seat alternation

To eliminate first-player advantage bias, seats alternate every game:

- **Even game_index** (0, 2, 4, ...): Agent A sits in seat 0 (goes first)
- **Odd game_index** (1, 3, 5, ...): Agent B sits in seat 0 (goes first)

All analysis functions account for this. The `first_player` field in
`GameResult` records which arrangement was used (0 = A first, 1 = B first).

### Determinism

Every game is fully deterministic given a seed. Game `i` uses seed
`base_seed + i`. Agent RNG seeds are also derived from the game seed. Running
the same configuration twice produces identical results, whether serial or
parallel.

### Key source files

| File | Purpose |
|------|---------|
| `src/simulation/runner.py` | `SimulationRunner`, `_run_single_game`, `AGENT_REGISTRY` |
| `src/simulation/results.py` | `GameResult`, `MatchupResult`, CSV I/O |
| `src/simulation/analysis.py` | All statistics functions and `summary_text` |
| `src/simulation/__init__.py` | Public exports |

---

## 5. Running Simulations

### Quick smoke test (seconds)

Confirm the framework works end-to-end with a tiny run:

```python
from src.simulation.runner import SimulationRunner
from src.simulation.analysis import summary_text

runner = SimulationRunner(
    agent_a_name="GreedyAgent",
    agent_b_name="RandomAgent",
    num_games=10,
    base_seed=42,
    fast_mode=True,       # fast: skip grey die
    num_workers=1,        # serial
    progress_interval=5,
)
result = runner.run()
print(summary_text(result))
```

Save as `smoke_test.py` and run:
```bash
pypy3 smoke_test.py
```

This should complete in under a minute and print a summary report.

### Production run: single matchup

```python
from src.simulation.runner import SimulationRunner
from src.simulation.results import save_results_csv
from src.simulation.analysis import summary_text

runner = SimulationRunner(
    agent_a_name="GreedyAgent",
    agent_b_name="RandomAgent",
    num_games=1000,
    base_seed=0,
    fast_mode=False,      # production: include grey die
    num_workers=12,       # adjust to your CPU core count
    progress_interval=100,
)
result = runner.run()

save_results_csv(result, "results/greedy_vs_random.csv")
print(summary_text(result))
```

### Production run: all matchups

```python
import os
from multiprocessing import cpu_count
from src.simulation.runner import SimulationRunner
from src.simulation.results import save_results_csv
from src.simulation.analysis import summary_text

MATCHUPS = [
    ("RandomAgent",       "RandomAgent"),
    ("GreedyAgent",       "RandomAgent"),
    ("HeuristicAgent",    "RandomAgent"),
    ("ConservativeAgent", "RandomAgent"),
    ("GreedyAgent",       "HeuristicAgent"),
    ("GreedyAgent",       "ConservativeAgent"),
    ("GreedyAgent",       "GreedyAgent"),
]

NUM_GAMES = 1000
BASE_SEED = 0
FAST_MODE = False          # production mode
NUM_WORKERS = cpu_count()  # use all CPU cores
OUTPUT_DIR = "results"

os.makedirs(OUTPUT_DIR, exist_ok=True)

for agent_a, agent_b in MATCHUPS:
    print(f"\n{'='*60}")
    print(f"  {agent_a} vs {agent_b}")
    print(f"{'='*60}\n")

    runner = SimulationRunner(
        agent_a_name=agent_a,
        agent_b_name=agent_b,
        num_games=NUM_GAMES,
        base_seed=BASE_SEED,
        fast_mode=FAST_MODE,
        num_workers=NUM_WORKERS,
        progress_interval=100,
    )
    result = runner.run()

    filename = f"{agent_a.lower()}_vs_{agent_b.lower()}.csv"
    save_results_csv(result, os.path.join(OUTPUT_DIR, filename))
    print(summary_text(result))
    print()
```

### Performance estimates (PyPy, 12 cores)

| Mode | 1,000 games | Notes |
|------|-------------|-------|
| fast_mode=True  | ~20 minutes | Good for testing hypotheses |
| fast_mode=False | ~3.5 hours  | Required for production results |

RandomAgent-only matchups are much faster (no probability calculation).
GreedyAgent matchups are the bottleneck.

### SimulationRunner parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `agent_a_name` | str | (required) | Name from AGENT_REGISTRY |
| `agent_b_name` | str | (required) | Name from AGENT_REGISTRY |
| `num_games` | int | (required) | Total games to simulate |
| `base_seed` | int | 0 | First game uses this seed; game i uses base_seed + i |
| `fast_mode` | bool | True | False = include grey die (~1M outcomes per decision) |
| `num_workers` | int | 1 | 1 = serial; >1 = multiprocessing pool |
| `progress_interval` | int | 100 | Print progress every N games |

Valid agent names: `RandomAgent`, `GreedyAgent`, `BoundedGreedyAgent`, `HeuristicAgent`, `ConservativeAgent`.

---

## 6. Understanding the Output

### Summary report

`summary_text(matchup)` prints a report like this:

```
Matchup: GreedyAgent vs RandomAgent
Games: 1000 (seed 0, fast_mode=False)
Elapsed: 12543.2s

Wins: GreedyAgent=623, RandomAgent=341, ties=36
Win rate (GreedyAgent): 0.646 [0.614, 0.678]

Mean scores: GreedyAgent=12.45, RandomAgent=8.31
Std dev: GreedyAgent=4.12, RandomAgent=3.89
CV: GreedyAgent=0.331, RandomAgent=0.468
Mean score advantage (GreedyAgent): +4.14

Paired t-test: t=18.432, p=0.0000
First-player win rate: 0.523
```

### Line-by-line explanation

**Line 1: `Matchup`** -- Which agents were compared. Agent A is always named
first.

**Line 2: `Games`** -- Total games played, the base seed used, and whether
fast_mode was on. Production results should always show `fast_mode=False`.

**Line 3: `Elapsed`** -- Wall-clock seconds for the entire batch.

**Line 5: `Wins`** -- Raw win counts for each agent, plus tie count. A game is
a tie when both players end with the same coin total. Wins + losses + ties =
total games.

**Line 6: `Win rate`** -- Agent A's win rate among decisive (non-tie) games,
with 95% Wald confidence interval in brackets. This is the primary metric for
RQ1.

- The rate is calculated as: `A_wins / (A_wins + B_wins)`. Ties are excluded.
- The confidence interval uses the Wald formula: `rate +/- 1.96 * sqrt(rate * (1 - rate) / N_decisive)`.
- For 1,000 games, the CI width is typically +/-3%. For 5,000 games, +/-1.4%.

**Line 8: `Mean scores`** -- Average final coin count for each agent across
all games. Accounts for seat alternation.

**Line 9: `Std dev`** -- Standard deviation of final scores (Bessel's
correction, dividing by N-1). Higher std dev = more volatile outcomes.

**Line 10: `CV`** -- Coefficient of variation (std / mean). This is RQ2.
Higher CV = more luck-driven. A CV above 0.5 suggests outcomes are heavily
influenced by randomness.

**Line 11: `Mean score advantage`** -- Agent A's mean score minus Agent B's
mean score. This is RQ3. Positive means Agent A outscores on average.

**Line 13: `Paired t-test`** -- Tests whether the mean score difference is
statistically significant.

- `t`: The t-statistic. Larger absolute value = stronger evidence of a
  real difference.
- `p`: Two-tailed p-value. If p < 0.05, the score difference is
  statistically significant at the 95% level. For large N, uses normal
  approximation via `math.erfc`.

**Line 14: `First-player win rate`** -- Fraction of decisive games won by the
player in seat 0 (who takes the first turn). If this is close to 0.50, there
is no meaningful first-player advantage. Values above 0.55 would suggest a
structural bias in the game.

### CSV output

`save_results_csv(matchup, filepath)` writes one row per game:

| Column | Type | Description |
|--------|------|-------------|
| `game_index` | int | 0-based game number |
| `seed` | int | Seed used for this game |
| `score_0` | int | Final coins for seat 0 |
| `score_1` | int | Final coins for seat 1 |
| `winner` | int or "tie" | Winning seat index, or "tie" |
| `num_legs` | int | Number of legs in the game |
| `num_turns` | int | Total turns taken |
| `agent_seat_0` | str | Agent name in seat 0 |
| `agent_seat_1` | str | Agent name in seat 1 |
| `first_player` | int | 0 = Agent A was seat 0, 1 = Agent B was seat 0 |

The CSV can be loaded back with `load_results_csv(filepath)` for further
analysis, or opened in pandas / Excel for custom exploration.

### Individual analysis functions

All functions are in `src.simulation.analysis` and take a `MatchupResult`:

| Function | Returns | Description |
|----------|---------|-------------|
| `agent_a_wins(m)` | int | Games won by agent A |
| `agent_b_wins(m)` | int | Games won by agent B |
| `tie_count(m)` | int | Games ending in tie |
| `win_rate_with_ci(m)` | (float, float, float) | (rate, ci_lo, ci_hi) for agent A |
| `mean_scores(m)` | (float, float) | (A mean, B mean) |
| `score_std_dev(m)` | (float, float) | (A std, B std) |
| `coefficient_of_variation(m)` | (float, float) | (A CV, B CV) |
| `mean_score_advantage(m)` | float | A mean - B mean |
| `t_test_scores(m)` | (float, float) | (t-statistic, p-value) |
| `first_player_win_rate(m)` | float | Seat-0 win fraction |
| `summary_text(m)` | str | Full human-readable report |

---

## 7. Verifying Results

### Sanity check 1: Automated tests pass

```bash
pypy3 -m pytest tests/test_simulation.py -v
```

All 33 tests should pass. These verify:
- Data class immutability and field correctness (7 tests)
- CSV round-trip integrity including tie handling (3 tests)
- Runner determinism, parallelism, seat alternation, all agent types (10 tests)
- Analysis functions against hand-computed values (11 tests)
- Full pipeline and mirror-matchup statistical bounds (2 tests)

### Sanity check 2: Determinism

Run the same configuration twice and compare results:

```python
from src.simulation.runner import SimulationRunner

kwargs = dict(
    agent_a_name="RandomAgent",
    agent_b_name="RandomAgent",
    num_games=50,
    base_seed=42,
    fast_mode=True,
    num_workers=1,
)
r1 = SimulationRunner(**kwargs).run()
r2 = SimulationRunner(**kwargs).run()

for g1, g2 in zip(r1.games, r2.games):
    assert g1.scores == g2.scores
    assert g1.winner == g2.winner
print("Determinism check passed")
```

Parallel runs (num_workers > 1) also produce identical results because output
is sorted by game_index after collection.

### Sanity check 3: Random vs Random baseline

The RandomAgent vs RandomAgent matchup should produce:

- Win rate near 0.50 (within 95% CI of 0.50)
- Mean score advantage near 0 (within +/-1 coin)
- t-test p-value > 0.05 (no significant difference)
- First-player win rate near 0.50

If any of these are far off, something is wrong with seat alternation or the
game engine.

### Sanity check 4: Greedy should beat Random

The GreedyAgent vs RandomAgent matchup should show:

- Win rate meaningfully above 0.50
- Positive mean score advantage
- t-test p-value < 0.05 (statistically significant)

If the GreedyAgent does not beat RandomAgent, the EV calculations may be
broken. Re-run the probability validation tests:

```bash
pypy3 -m pytest tests/test_probability_validation.py -v
```

### Sanity check 5: CSV round-trip

```python
from src.simulation.results import save_results_csv, load_results_csv
from src.simulation.analysis import summary_text

# ... after running a simulation and getting `result` ...
save_results_csv(result, "/tmp/check.csv")
loaded = load_results_csv("/tmp/check.csv")

for orig, loaded_g in zip(result.games, loaded.games):
    assert orig.scores == loaded_g.scores
    assert orig.winner == loaded_g.winner
print("CSV round-trip check passed")
```

### Sanity check 6: Game length is reasonable

Inspect a few games from any matchup:

```python
for g in result.games[:5]:
    print(f"Game {g.game_index}: {g.num_legs} legs, {g.num_turns} turns, "
          f"scores={g.scores}, winner={g.winner}")
```

Typical Camel Up games last 2--5 legs and 15--40 turns. If games consistently
show 1 leg or 100+ turns, investigate.

### Sanity check 7: Seat alternation is correct

```python
for g in result.games[:10]:
    expected_fp = 0 if g.game_index % 2 == 0 else 1
    assert g.first_player == expected_fp
print("Seat alternation check passed")
```

---

## 8. Expected Results

These are rough expectations based on agent design and game theory reasoning.
Actual numbers will vary. Use fast_mode=True with 200+ games to get
preliminary estimates, then confirm with fast_mode=False and 1,000+ games.

### Matchup 1: RandomAgent vs RandomAgent

| Metric | Expected range | Reasoning |
|--------|---------------|-----------|
| Win rate | 0.47--0.53 | Symmetric matchup, no skill difference |
| Mean score advantage | -0.5 to +0.5 | No systematic edge |
| t-test p-value | > 0.05 | No significant difference |
| CV | 0.3--0.6 | Reflects inherent game variance |
| First-player win rate | 0.48--0.55 | Possible small first-mover advantage |

This matchup establishes the baseline variance. If the CV here is 0.4 and
the same CV appears in GreedyAgent runs, luck dominates even with strategy.

### Matchup 2: GreedyAgent vs RandomAgent (primary)

| Metric | Expected range | Reasoning |
|--------|---------------|-----------|
| Win rate | 0.55--0.75 | EV optimization should help, but dice are random |
| Mean score advantage | +2 to +6 coins | Better bets accumulate small edges |
| t-test p-value | < 0.001 | Strong statistical significance at 1,000 games |
| CV (GreedyAgent) | 0.25--0.45 | Possibly lower than RandomAgent's CV |

This is the key matchup. Where the win rate falls on the spectrum determines
whether Camel Up is luck-dominated or skill-influenced:

- **0.50--0.55**: Predominantly luck. Similar to blackjack.
- **0.55--0.65**: Moderate skill. Similar to poker.
- **0.65--0.75**: Meaningful skill. Similar to backgammon.

### Matchup 3: HeuristicAgent vs RandomAgent

| Metric | Expected range | Reasoning |
|--------|---------------|-----------|
| Win rate | 0.52--0.65 | Simple rules capture some but not all edge |
| Mean score advantage | +1 to +4 coins | Less precise than GreedyAgent |

The gap between this win rate and GreedyAgent's win rate measures how much
exact calculation adds beyond simple heuristics.

### Matchup 4: ConservativeAgent vs RandomAgent

| Metric | Expected range | Reasoning |
|--------|---------------|-----------|
| Win rate | 0.50--0.60 | Risk-aversion helps but misses opportunities |
| CV (ConservativeAgent) | 0.20--0.35 | Lower variance due to safe play |

ConservativeAgent should have the lowest CV because it avoids risky bets and
prefers the guaranteed +1 pyramid ticket.

### Matchup 5: GreedyAgent vs HeuristicAgent

| Metric | Expected range | Reasoning |
|--------|---------------|-----------|
| Win rate | 0.52--0.62 | Greedy's edge over heuristic should be smaller than over random |

This measures the marginal value of exact probability calculation over
rule-of-thumb play.

### Matchup 7: GreedyAgent vs GreedyAgent

| Metric | Expected range | Reasoning |
|--------|---------------|-----------|
| Win rate | 0.47--0.53 | Symmetric -- should be balanced |
| CV | 0.25--0.45 | Shows irreducible game variance even with optimal play |

This is important for RQ2. The CV in this matchup represents the floor of
variance -- the luck that cannot be eliminated even with perfect strategy.
If this CV is close to the RandomAgent vs RandomAgent CV, then strategy
barely reduces variance.

### Decision framework

After collecting results from all matchups, answer the research questions:

**RQ1** (Win rate): Read the `Win rate` line from Matchup 2 (GreedyAgent vs
RandomAgent). Place it on the reference spectrum. If 0.50--0.55, Camel Up is
luck-dominated. If 0.60+, skill matters.

**RQ2** (CV): Compare `CV` across all matchups. If skilled agents have much
lower CV than RandomAgent, strategy reduces volatility. If CV is similar
across all agents, the dice dominate outcomes regardless of strategy.

**RQ3** (Score advantage): Read `Mean score advantage` from Matchup 2. This is
the average coin benefit of optimal play per game. Express it as a percentage
of the RandomAgent's mean score to normalize.

**RQ4** (Comparison): Plot the GreedyAgent win rate alongside the reference
games in Section 1. Classify Camel Up on the skill-luck spectrum.

### Confidence interval guidance

| Games | Typical 95% CI width | Sufficient for |
|-------|---------------------|----------------|
| 200 | +/-7% | Preliminary estimates, smoke testing |
| 1,000 | +/-3% | Standard production run |
| 5,000 | +/-1.4% | High-precision results |
| 10,000 | +/-1% | Publication-quality confidence |

If your CI from 1,000 games is too wide to distinguish between "luck" and
"moderate skill" (e.g., CI spans 0.50 to 0.60), increase to 5,000 games.

---

## 9. Troubleshooting

### "Unknown agent" ValueError

```
ValueError: Unknown agent: OptimalAgent
```

Only four agent names are registered: `RandomAgent`, `GreedyAgent`,
`HeuristicAgent`, `ConservativeAgent`. Check spelling and capitalization.

### Simulation is very slow

- Confirm you are using **pypy3**, not python3. PyPy is 6--10x faster.
- Use `num_workers` equal to your CPU core count for parallelism.
- Use `fast_mode=True` for initial testing, then switch to `fast_mode=False`
  for final production results.
- RandomAgent-only matchups are nearly instant. GreedyAgent matchups are slow
  because each decision enumerates up to 1 million outcomes.

### Results differ between serial and parallel

They should not. Both modes use the same seeds and sort by game_index. If you
observe differences, verify you are using the same `base_seed`, `num_games`,
and `fast_mode` for both runs.

### Import errors

Run from the project root directory:

```bash
cd /path/to/camelup
pypy3 your_script.py
```

The project uses `src.` import paths that require the working directory to be
the repository root.

### Memory issues with large runs

Each `GameResult` is small (~200 bytes). 10,000 games require ~2 MB. Memory
should not be an issue. If running into problems, reduce `num_workers` (each
worker holds its own copy of the game engine in memory).

### CSV file is empty or has wrong columns

The expected header is:
```
game_index,seed,score_0,score_1,winner,num_legs,num_turns,agent_seat_0,agent_seat_1,first_player
```

If the header differs, the `load_results_csv` function will fail.
`save_results_csv` and `load_results_csv` are tested for round-trip
correctness in `tests/test_simulation.py::TestCSVRoundTrip`.

---

## 10. Limitations of Current Results

The CSV files in `results/` were generated with the following constraints:

### fast_mode=True (grey die excluded)

All results use `fast_mode=True`, which skips the grey die (crazy camels) in
probability calculations. This reduces the enumeration from ~1,049,760
outcomes per decision to 29,160 -- a 36x speedup that made the runs feasible.

With `fast_mode=False`, a single GreedyAgent game takes 10+ minutes (PyPy, 12
cores), making 1,000-game matchups require days of compute. The `fast_mode=True`
results are still meaningful because:

- The grey die affects crazy camels, which do not count toward race rankings.
- The EV calculations for leg bets and overall bets still use exact enumeration
  of all 5 racing dice.
- The primary skill signal (which camel to bet on, when to bet) is captured.

However, `fast_mode=False` results may differ because crazy camel movement
affects spectator tile payouts and can shift racing camel positions via stacking.
A future run with `fast_mode=False` on more powerful hardware would provide the
definitive numbers.

### 1,000 games per matchup (not 10,000)

The initial plan called for adaptive N starting at 1,000 and scaling to 10,000
if confidence intervals were too wide. At 1,000 games, the 95% CI width is
roughly +/-3% for balanced matchups. For the dominant matchups (Greedy vs
Random at 99.8%), 1,000 games is more than sufficient.

For the closer matchups (Greedy vs Conservative at 74.1%), the CI is
[0.714, 0.769], which is narrow enough to draw clear conclusions. Scaling to
10,000 games would tighten this to +/-1% but is unlikely to change the
qualitative findings.

### Compute environment

Results were generated on a 12-core Apple Silicon Mac with PyPy 3.10. Total
wall-clock time for all 7 two-player matchups: ~57 minutes. A dedicated server
or cloud instance with more cores could run the full `fast_mode=False` suite in
reasonable time.

---

## 11. N-Player Simulations

### Overview

The N-player framework tests whether skill advantage scales with player count.
It uses a **focal-vs-field** model: one focal agent vs N-1 identical opponents.
This is a different statistical framework than the 2-player paired A-vs-B
comparison, so it uses separate modules.

### Key differences from 2-player

| Feature | 2-Player | N-Player |
|---------|----------|----------|
| Analysis model | A vs B paired comparison | Focal vs field |
| Seat rotation | Even/odd alternation | Game i -> focal in seat i % N |
| Win rate baseline | 0.50 | 1/N |
| t-test | Paired t-test (A-B diffs) | One-sample t-test (focal - field_mean diffs) |
| Runner | `SimulationRunner` | `NPlayerRunner` |
| Results | `MatchupResult` | `NPlayerMatchupResult` |

### Running N-player simulations

```python
from src.simulation.n_player_runner import NPlayerRunner
from src.simulation.n_player_results import save_n_player_results_csv
from src.simulation.n_player_analysis import summary_text

runner = NPlayerRunner(
    focal_agent_name="GreedyAgent",
    field_agent_names=("RandomAgent", "RandomAgent", "RandomAgent"),
    num_games=1000,
    base_seed=0,
    fast_mode=True,
    num_workers=12,
    progress_interval=100,
)
result = runner.run()

save_n_player_results_csv(result, "results/greedy_vs_3xrandom_4p.csv")
print(summary_text(result))
```

### Production script

`run_n_player_simulation.py` runs all 6 N-player matchups (Greedy and
BoundedGreedy vs Random and Heuristic at 2P/4P/6P):

```bash
pypy3 run_n_player_simulation.py
```

### N-player CSV format

Columns are dynamic based on player count:
```
game_index,seed,score_0,...,score_{N-1},winner,num_legs,num_turns,agent_seat_0,...,agent_seat_{N-1},focal_seat
```

`load_n_player_results_csv()` auto-detects N from the number of `score_*` columns.

### N-player analysis functions

All in `src.simulation.n_player_analysis`, taking `NPlayerMatchupResult`:

| Function | Returns | Description |
|----------|---------|-------------|
| `focal_wins(r)` | int | Games won by focal agent |
| `focal_losses(r)` | int | Games lost by focal agent |
| `tie_count(r)` | int | Tied games |
| `focal_win_rate_with_ci(r)` | (rate, lo, hi) | 95% Wald CI, ties excluded |
| `baseline_win_rate(r)` | float | 1/N (no-skill baseline) |
| `focal_mean_score(r)` | float | Focal agent's mean score |
| `field_mean_score(r)` | float | Mean of all non-focal scores |
| `mean_score_advantage(r)` | float | focal - field mean |
| `focal_score_std_dev(r)` | float | Bessel's correction |
| `focal_coefficient_of_variation(r)` | float | std/mean |
| `t_test_focal_vs_field(r)` | (t, p) | One-sample t on per-game diffs |
| `seat_win_rates(r)` | Tuple[float,...] | Win rate per seat position |
| `summary_text(r)` | str | Human-readable summary |

### N-player results

#### Greedy vs Random (skill does NOT decay with player count)

| Players | Win Rate | Baseline (1/N) | WR / Baseline | Score Advantage |
|---------|----------|----------------|---------------|-----------------|
| 2P | 0.998 | 0.500 | 2.0x | +61.12 |
| 4P | 0.981 | 0.250 | 3.9x | +38.34 |
| 6P | 0.963 | 0.167 | 5.8x | +30.32 |

#### Greedy vs Heuristic

| Players | Win Rate | Baseline (1/N) | WR / Baseline | Score Advantage |
|---------|----------|----------------|---------------|-----------------|
| 2P | 0.863 | 0.500 | 1.7x | +11.49 |
| 4P | 0.871 | 0.250 | 3.5x | +12.02 |
| 6P | 0.829 | 0.167 | 5.0x | +10.30 |

#### BoundedGreedy vs Heuristic (bounded rationality)

| Players | Win Rate | Baseline (1/N) | WR / Baseline | Score Advantage |
|---------|----------|----------------|---------------|-----------------|
| 2P | 0.879 | 0.500 | 1.8x | +13.11 |
| 4P | 0.862 | 0.250 | 3.4x | +11.26 |
| 6P | 0.756 | 0.167 | 4.5x | +8.74 |

#### Key findings

- **Skill does NOT decay toward 1/N.** Relative to baseline, GreedyAgent's
  advantage actually increases with more players (2.0x at 2P to 5.8x at 6P vs
  Random). More weak opponents = more value to extract.
- **Bounded rationality effect at 6P.** BoundedGreedy (depth=2) matches
  FullGreedy at 2P/4P but drops 7.3pp at 6P (75.6% vs 82.9%). Shallow
  calculation loses resolution when many opponents create noise.
- **Skill still dominant.** Even depth-limited BoundedGreedy wins 4.5x baseline
  at 6P. Probability calculation provides a commanding advantage at all player
  counts.
