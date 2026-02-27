from __future__ import annotations

from typing import TypeAlias

import discord

from .bot import Zenox


Interaction: TypeAlias = discord.Interaction[Zenox]
User: TypeAlias = discord.User | discord.Member | None
