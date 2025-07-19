from __future__ import annotations

from zenox.static.enums import Game

GI_ICON = "https://iili.io/FjBBRIV.png"
HSR_ICON = "https://iili.io/FjBqpqX.png"
ZZZ_ICON = "https://iili.io/FjBqoRR.jpg"

def get_game_icon(game: Game) -> str:
    """Returns the icon URL for the given game."""
    if game == Game.GENSHIN:
        return GI_ICON
    elif game == Game.STARRAIL:
        return HSR_ICON
    elif game == Game.ZZZ:
        return ZZZ_ICON
    else:
        raise ValueError(f"Unsupported game: {game}")