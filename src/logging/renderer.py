"""Board and state rendering for human-readable game logs."""

from ..game.board import Board, TRACK_LENGTH, FINISH_LINE
from ..game.camel import CamelColor, RACING_CAMELS, CRAZY_CAMELS
from ..game.dice import Pyramid


# Short display names for camels
_CAMEL_NAMES = {
    CamelColor.BLUE: "Blu",
    CamelColor.GREEN: "Grn",
    CamelColor.YELLOW: "Yel",
    CamelColor.RED: "Red",
    CamelColor.PURPLE: "Pur",
    CamelColor.WHITE: "*Wht",
    CamelColor.BLACK: "*Blk",
}

# Full display names for ranking
_CAMEL_FULL_NAMES = {
    CamelColor.BLUE: "Blue",
    CamelColor.GREEN: "Green",
    CamelColor.YELLOW: "Yellow",
    CamelColor.RED: "Red",
    CamelColor.PURPLE: "Purple",
    CamelColor.WHITE: "White",
    CamelColor.BLACK: "Black",
}

_ORDINALS = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th"}


def _camel_display(camel):
    """Short display name for a camel."""
    return _CAMEL_NAMES.get(camel, camel.value)


def render_board(board):
    """
    Render the board as a compact text string.

    Format: [1:Grn>Pur][2:Blu>Red][3:Yel][4:][5:]...[16:*Blk]
    Camels listed bottom to top, separated by '>'.
    Crazy camels prefixed with '*'.
    Finished camels shown as FINISHED.
    Spectator tiles on a separate line below.
    """
    parts = []
    for space in range(1, TRACK_LENGTH + 1):
        stack = board.get_stack_at(space)
        if stack:
            camels_str = ">".join(_camel_display(c) for c in stack.camels)
            parts.append(f"[{space}:{camels_str}]")
        else:
            parts.append(f"[{space}:]")

    # Show finished camels
    finished = []
    for space in range(FINISH_LINE, FINISH_LINE + 5):
        stack = board.get_stack_at(space)
        if stack:
            for camel in stack.camels:
                finished.append(f"{_camel_display(camel)}(sp{space})")

    lines = ["Board: " + "".join(parts)]
    if finished:
        lines.append("FINISHED: " + ", ".join(finished))

    # Spectator tiles
    if board.spectator_tiles:
        tile_parts = []
        for space in sorted(board.spectator_tiles.keys()):
            tile = board.spectator_tiles[space]
            side = "cheering(+1)" if tile.is_cheering else "booing(-1)"
            tile_parts.append(f"space {space} {side} by P{tile.owner}")
        lines.append("Spectator tiles: " + ", ".join(tile_parts))

    return "\n".join(lines)


def render_scores(players):
    """
    Render player scores.

    Format: Scores: P0=3, P1=5
    """
    parts = [f"P{i}={p.coins}" for i, p in enumerate(players)]
    return "Scores: " + ", ".join(parts)


def render_ranking(board):
    """
    Render the current camel ranking.

    Format: Ranking: Red 1st, Green 2nd, Yellow 3rd, Blue 4th, Purple 5th
    """
    ranking = board.get_ranking()
    parts = []
    for i, camel in enumerate(ranking):
        ordinal = _ORDINALS.get(i + 1, f"{i + 1}th")
        parts.append(f"{_CAMEL_FULL_NAMES[camel]} {ordinal}")
    return "Ranking: " + ", ".join(parts)


def render_pyramid(pyramid):
    """
    Render remaining dice in pyramid.

    Format: Remaining dice: Blue, Green, Yellow | Grey: available
    """
    racing_names = []
    for die in sorted(pyramid.remaining, key=lambda d: d.value):
        racing_names.append(die.value.capitalize())

    grey_status = "available" if not pyramid.grey_rolled else "rolled"
    if racing_names:
        return f"Remaining dice: {', '.join(racing_names)} | Grey: {grey_status}"
    else:
        return f"Remaining dice: (none) | Grey: {grey_status}"
