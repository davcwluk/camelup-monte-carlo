# Testing Plan: Rule Verification

This document maps each rule from the Camel Up rulebook to specific test cases to verify the code implementation is correct.

**Last Updated:** 206 tests across 11 test files (Phases 1-3 + pre-Phase 4 validation + game logger)

---

## 1. Dice Mechanics

### 1.1 Racing Dice
| Rule | Test Case | Status |
|------|-----------|--------|
| Each racing die has 6 faces: 1, 1, 2, 2, 3, 3 | `test_racing_die_faces` | PASS |
| Each value (1, 2, 3) has equal probability (1/3) | `test_racing_die_distribution` | PASS |
| Rolling a die returns value 1, 2, or 3 | `test_roll_racing_die_returns_valid_value` | PASS |

### 1.2 Grey Die
| Rule | Test Case | Status |
|------|-----------|--------|
| Grey die has 6 faces (3 white, 3 black) | `test_grey_die_faces` | PASS |
| White numbers move white camel | `test_roll_grey_die_returns_valid_result` | PASS |
| Black numbers move black camel | `test_roll_grey_die_returns_valid_result` | PASS |

### 1.3 Pyramid
| Rule | Test Case | Status |
|------|-----------|--------|
| Pyramid starts with all 5 racing dice + grey die | `test_initial_pyramid_has_all_dice` | PASS |
| Rolling removes die from pyramid | `test_roll_from_pyramid_removes_die` | PASS |
| Leg ends when 5 of 6 dice revealed (1 remains) | `test_leg_complete_when_one_die_remains` | PASS |
| Pyramid resets at start of new leg | `test_reset_pyramid` | PASS |

---

## 2. Camel Movement

### 2.1 Basic Movement
| Rule | Test Case | Status |
|------|-----------|--------|
| Racing camels move clockwise (forward) | `test_racing_camel_moves_forward` | PASS |
| Camel moves exactly the number shown on die | `test_camel_moves_exact_spaces` | PASS |
| Camel crossing space 16 finishes the race | `test_camel_finishes_race` | PASS |
| Detect any camel finished | `test_any_camel_finished_detection` | PASS |

### 2.2 Camel Stacking
| Rule | Test Case | Status |
|------|-----------|--------|
| Camels on same space form a stack | `test_camels_form_stack` | PASS |
| Camel landing on occupied space goes ON TOP | `test_camel_lands_on_top` | PASS |
| Moving camel carries ALL camels above it | `test_moving_camel_carries_stack` | PASS |
| Camels below the moving camel stay in place | `test_camels_below_stay_in_place` | PASS |
| Higher in stack = ahead in ranking (same space) | `test_stack_ranking` | PASS |
| Stack lands on existing stack (merges on top) | `test_stack_lands_on_existing_stack` | PASS |
| Large stack (5+) moves correctly | `test_large_stack_movement` | PASS |

### 2.3 Crazy Camels
| Rule | Test Case | Status |
|------|-----------|--------|
| Crazy camels move counter-clockwise (backward) | `test_crazy_camel_moves_backward` | PASS |
| Crazy camels can carry racing camels backward | `test_crazy_camel_carries_racing_camels_backward` | PASS |
| Crazy camels are ignored for ranking | `test_ranking_ignores_crazy_camels` | PASS |
| Crazy camel lands on racing camel | `test_crazy_camel_lands_on_racing_camel` | PASS |
| Crazy camel at space 1 boundary | `test_crazy_camel_at_space_1_boundary` | PASS |
| Racing camel on crazy carried backward | `test_racing_camel_on_crazy_carried_backward` | PASS |
| If only one crazy camel has racers on back, move that one | `test_crazy_camel_priority_rule` | PASS |
| If crazy camels stacked (no racers), move top one | `test_crazy_camel_stack_rule` | PASS |

---

## 3. Spectator Tiles

### 3.1 Placement Rules
| Rule | Test Case | Status |
|------|-----------|--------|
| Cannot place on space 1 | `test_cannot_place_tile_on_space_1` | PASS |
| Cannot place on space 0 (invalid) | `test_cannot_place_tile_on_space_0` | PASS |
| Cannot place beyond track | `test_cannot_place_tile_beyond_track` | PASS |
| Can place on empty space (2-16) | `test_can_place_tile_on_empty_space` | PASS |
| Cannot place on space with camels | `test_cannot_place_tile_on_space_with_camels` | PASS |
| Cannot place adjacent to another tile | `test_cannot_place_tile_adjacent_to_another_tile` | PASS |
| Cannot place on existing tile | `test_cannot_place_tile_on_existing_tile` | PASS |
| Can place on cheering (+1) or booing (-1) side | `test_tile_has_two_sides` | PASS |
| Moving tile removes it from old position | `test_moving_tile_removes_from_old_position` | PASS |
| Can move own tile to adjacent space | `test_can_move_own_tile_to_adjacent_space` | PASS |
| Can re-place own tile on same space (switch sides) | `test_can_move_own_tile_to_same_space` | PASS |

### 3.2 Tile Effects
| Rule | Test Case | Status |
|------|-----------|--------|
| Cheering tile: camel moves +1 extra space | `test_cheering_tile_adds_one_space` | PASS |
| Booing tile: camel moves -1 space (backward) | `test_booing_tile_subtracts_one_space` | PASS |
| Cheering tile: camel lands ON TOP at final space | `test_cheering_tile_lands_on_top` | PASS |
| Booing tile: camel goes UNDERNEATH at final space | `test_booing_tile_lands_underneath` | PASS |
| Tile owner receives 1 coin when camel lands | `test_tile_owner_receives_one_coin` | PASS |
| Tile effect applies to entire moving stack | `test_tile_effect_with_stack` | PASS |

---

## 4. Betting Tickets (Leg Betting)

### 4.1 Taking Tickets
| Rule | Test Case | Status |
|------|-----------|--------|
| 4 tickets per camel color (values 5, 3, 2, 2) | `test_ticket_values_are_5_3_2_2` | PASS |
| 4 tickets per camel | `test_four_tickets_per_camel` | PASS |
| Must take top ticket (highest available value) | `test_take_top_ticket_gets_highest_value` | PASS |
| Can take multiple tickets for same camel | `test_can_take_multiple_tickets_same_camel` | PASS |
| Ticket removed from stack when taken | `test_ticket_removed_when_taken` | PASS |
| No ticket when all taken | `test_no_ticket_available_when_all_taken` | PASS |
| Get all available tickets | `test_get_all_available_tickets` | PASS |

### 4.2 Pyramid Tickets
| Rule | Test Case | Status |
|------|-----------|--------|
| Pyramid ticket increments count | `test_pyramid_ticket_increments_count` | PASS |
| Pyramid tickets tracked per player | `test_pyramid_tickets_per_player` | PASS |

### 4.3 Leg Scoring
| Rule | Test Case | Status |
|------|-----------|--------|
| 1st place bet: earn ticket value (5, 3, 2, or 2) | `test_first_place_bet_earns_ticket_value` | PASS |
| 2nd place bet: earn 1 coin | `test_second_place_bet_earns_one` | PASS |
| 3rd-5th place bet: lose 1 coin | `test_other_place_bet_loses_one` | PASS |
| Pyramid tickets: earn 1 coin each | `test_pyramid_ticket_earns_one_each` | PASS |
| Combined scoring works | `test_combined_leg_scoring` | PASS |
| Tickets returned to stacks after leg scoring | `test_tickets_reset_after_leg` | PASS |

---

## 5. Overall Winner/Loser Betting

### 5.1 Placing Bets
| Rule | Test Case | Status |
|------|-----------|--------|
| Each player has 5 finish cards (one per camel) | `test_player_has_five_finish_cards` | PASS |
| Using a card removes it (can't bet same camel twice) | `test_finish_card_removed_when_used` | PASS |
| Cards placed face-down (secret) | N/A - UI concern | - |
| Can bet on winner OR loser with same card | `test_can_bet_winner_or_loser` | PASS |

### 5.2 End Game Scoring
| Rule | Test Case | Status |
|------|-----------|--------|
| Payouts are 8, 5, 3, 2, 1, 1, 1, 1 | `test_overall_payouts_structure` | PASS |
| 1st correct winner bet: +8 coins | `test_first_correct_winner_bet_earns_eight` | PASS |
| 2nd correct winner bet: +5 coins | `test_second_correct_winner_bet_earns_five` | PASS |
| Correct order matters (8, 5, 3, 2, 1) | `test_correct_winner_bet_order_matters` | PASS |
| Wrong winner bet: -1 coin | `test_wrong_winner_bet_loses_one` | PASS |
| Same rules apply for loser bets | `test_loser_bet_scoring_same_as_winner` | PASS |
| Overall bets preserved after leg reset | `test_overall_bets_preserved_after_leg_reset` | PASS |

---

## 6. Game Flow

### 6.1 Turn Structure
| Rule | Test Case | Status |
|------|-----------|--------|
| Player must take exactly 1 action per turn | `test_one_action_per_turn` | PASS |
| 4 possible actions available | `test_four_action_types_available` | PASS |
| Turn passes clockwise to next player | `test_turn_passes_clockwise` | PASS |
| No actions when game over | `test_no_actions_when_game_over` | PASS |

### 6.2 Leg End
| Rule | Test Case | Status |
|------|-----------|--------|
| Leg ends when 5 of 6 dice revealed | `test_leg_ends_when_five_dice_revealed` | PASS |
| Pyramid refilled after leg | `test_pyramid_refilled_after_leg` | PASS |
| Leg number increments | `test_leg_number_increments` | PASS |
| All betting tickets returned | `test_betting_tickets_returned_after_leg` | PASS |
| All spectator tiles returned to owners | `test_spectator_tiles_returned_after_leg` | PASS |
| Starting player = left of last pyramid ticket taker | `test_starting_player_rule` | PASS |

### 6.3 Game End
| Rule | Test Case | Status |
|------|-----------|--------|
| Game ends when any camel crosses finish line | `test_game_ends_when_camel_finishes` | PASS |
| Player with most coins wins | `test_most_coins_wins` | PASS |
| Tie = shared victory (returns None) | `test_tie_returns_none` | PASS |
| Get scores works | `test_get_scores` | PASS |

---

## 7. Player State

| Rule | Test Case | Status |
|------|-----------|--------|
| Player starts with 3 coins | `test_player_starts_with_three_coins` | PASS |
| Add coins works | `test_add_coins` | PASS |
| Player cannot go below 0 coins | `test_coins_cannot_go_below_zero` | PASS |
| Spectator tile tracking | `test_spectator_tile_tracking` | PASS |
| Can bet on overall checks cards | `test_can_bet_on_overall_checks_cards` | PASS |

---

## 8. Integration Tests

| Test | Status |
|------|--------|
| Complete game runs without errors | PASS |
| Game deterministic with same seed | PASS |
| Multiple legs can occur | PASS |
| Three-player game works | PASS |
| Four-player game works | PASS |
| Board move returns tile owner | PASS |
| Board game over detection | PASS |

---

## Summary

| Category | Implemented | Notes |
|----------|-------------|-------|
| Dice Mechanics | 10/10 | Complete |
| Basic Movement | 4/4 | Complete |
| Camel Stacking | 7/7 | Complete |
| Crazy Camels | 8/8 | Complete |
| Spectator Tiles | 17/17 | Complete (includes own-tile adjacency fix) |
| Betting Tickets | 15/15 | Complete |
| Overall Betting | 11/11 | Complete |
| Game Flow | 14/14 | Complete |
| Player State | 5/5 | Complete |
| Integration | 7/7 | Complete |
| **Subtotal** | **135 tests** | All rules implemented |

---

## All Rules Implemented

All rules from the rulebook have been implemented and tested.

---

## Test Files

### Rule Verification (Phase 1)
- `tests/test_dice.py` - 12 tests
- `tests/test_camel.py` - 28 tests (includes crazy camel priority/stack rule tests)
- `tests/test_game.py` - 9 tests
- `tests/test_betting.py` - 30 tests
- `tests/test_spectator.py` - 17 tests (includes own-tile adjacency fix)
- `tests/test_movement.py` - 20 tests
- `tests/test_game_flow.py` - 19 tests (includes starting player rule test)

### Probability and EV (Phase 2)
- `tests/test_probability.py` - 25 tests

### Agent Implementation (Phase 3)
- `tests/test_agents.py` - 23 tests (includes parallel performance benchmarks)

### Monte Carlo Validation (Pre-Phase 4)
- `tests/test_probability_validation.py` - 10 tests (2 marked slow; 2 test leg-stops-at-5-dice correctness)

### Game Logger
- `tests/test_game_logger.py` - 13 tests (renderer + integration)

**Note:** `tests/test_agents.py` has 1 additional test marked slow (full-mode greedy parallel benchmark). Total slow tests: 3.

**Total: 206 tests**
