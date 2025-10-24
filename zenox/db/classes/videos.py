from __future__ import annotations

import discord
from dataclasses import dataclass
from typing import Any, ClassVar, Dict

from ..mongodb import DB
from ...enums import Game

@dataclass
class Video:
    video_id: str
    game: Game
    title: str
    description: str