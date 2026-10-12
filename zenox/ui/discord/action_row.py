from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from .button import Button

if TYPE_CHECKING:
    from .select import Select, ChannelSelect, RoleSelect
    from .view import View

__all__ = ("ActionRow",)

class ActionRow[V: View](discord.ui.ActionRow):
    def __init__(self, *children: Button | Select | ChannelSelect | RoleSelect, id: int | None = None) -> None:
        super().__init__(*children, id=id)
        
        self.view: V
        self.children: list[Button | Select | ChannelSelect | RoleSelect]
    
    def translate(self, locale: discord.Locale) -> None:
        for child in self.children:
            child.translate(locale)
    
    def disable_items(self) -> None:
        for child in self.children:
            if child.custom_id is not None:
                self.view.item_states[child.custom_id] = child.disabled

                if isinstance(child, Button) and child.url:
                    continue

                child.disabled = True