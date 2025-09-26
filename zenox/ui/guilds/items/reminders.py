from __future__ import annotations

import discord
from typing import TYPE_CHECKING

from ...components import (
    ToggleButton,
    Button,
)
from zenox.embeds import DefaultEmbed
from zenox.l10n import LocaleStr

if TYPE_CHECKING:
    from ..view import GuildSettingsUI  # noqa: F401
    from ....types import Interaction


class StreamReminderToggle(ToggleButton["GuildSettingsUI"]):
    def __init__(self, current_toggle: bool):
        super().__init__(
            toggle_label=LocaleStr(
                key="guilds.reminders_module.edit.stream_reminder.label"
            ),
            current_toggle=current_toggle,
        )

    async def callback(self, i: Interaction):
        await super().callback(i)
        assert self.view.game is not None

        await self.view.guild._update_module_setting(
            module_name="reminders",
            game=self.view.game,
            setting="stream_reminder",
            value=self.current_toggle,
        )
        await self.view.update_ui(i)


class RemindersHelpButton(Button["GuildSettingsUI"]):
    def __init__(self):
        super().__init__(
            label=LocaleStr(key="guilds.reminders_module.help.button.label"),
            style=discord.ButtonStyle.primary,
            emoji="❔",
        )

    async def callback(self, i: Interaction):
        embed = DefaultEmbed(
            locale=self.view.locale,
            title=LocaleStr(key="guilds.reminders_module.help.title"),
        )
        embed.add_field(
            name=LocaleStr(key="guilds.reminders_module.help.stream_reminder.title"),
            value=LocaleStr(
                key="guilds.reminders_module.help.stream_reminder.description"
            ),
            inline=False,
        )
        await i.response.send_message(embed=embed, ephemeral=True)
