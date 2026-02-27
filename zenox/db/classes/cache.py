from __future__ import annotations

import discord
from dataclasses import dataclass
from typing import Any, ClassVar, Dict

from ..mongodb import DB

"""
identifier, who cached, data, timestamp"""

@dataclass
class CacheEntry:
    identifier: str
    cached_by: int
    data: Dict[str, Any]
    timestamp: int

    cache: ClassVar[Dict[str, CacheEntry]] = {}