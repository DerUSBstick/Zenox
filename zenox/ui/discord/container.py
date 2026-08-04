from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from zenox.utils.misc import is_valid_hex_color

from .action_row import ActionRow
from .section import Section
from .text_display import TextDisplay

if TYPE_CHECKING:
    from .view import LayoutView

__all__ = ("Container", "DefaultContainer")

type ContainerItem = (ActionRow | Section | TextDisplay | discord.ui.MediaGallery | discord.ui.File | discord.ui.Separator)

class Container[V: LayoutView](discord.ui.Container):
    def __init__(self, *children: ContainerItem, accent_color: discord.Color | int | str | None = None, spoiler: bool = False, id: int | None = None) -> None:
        if isinstance(accent_color, str):
            if not is_valid_hex_color(accent_color):
                raise ValueError(f"Invalid hex color: {accent_color}")
            accent_color = discord.Color(int(accent_color.lstrip("#"), 16))
        
        super().__init__(*children, accent_color=accent_color, spoiler=spoiler, id=id)

        self.view: V
    
    def translate(self, locale: discord.Locale) -> None:
        for child in self.children:
            if isinstance(child, (ActionRow, Section, TextDisplay)):
                child.translate(locale)
    
    def disable_items(self) -> None:
        for child in self.children:
            if isinstance(child, (ActionRow, Section)):
                child.disable_items()

class DefaultContainer[V: LayoutView](Container):
    def __init__(
        self,
        *children: ContainerItem,
        spoiler: bool = False,
        id: int | None = None,
    ) -> None:
        super().__init__(*children, accent_color=discord.Color(0xAF9878), spoiler=spoiler, id=id)
        
        self.view: V