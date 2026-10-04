from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from zenox import emojis, ui
from zenox.db.classes import Guild
from zenox.enums import Game
from zenox.l10n import LocaleStr

if TYPE_CHECKING:
    from zenox.types import Interaction

    from ..view import GuildSettingsView # noqa: F401

class StreamReminderToggle(ui.EmojiToggleButton["GuildSettingsView"]):
    def __init__(self, current_toggle: bool):
        super().__init__(
            current=current_toggle,
        )

    async def callback(self, i: Interaction):
        assert self.view.game is not None

        self.current = not self.current
        self.update_style()

        await self.view.guild._update_module_setting(
            module_name="reminders",
            game=self.view.game,
            setting="stream_reminder",
            value=self.current,
        )
        await self.view.update(i)

class ReminderNotificationSettingsContainer(ui.DefaultContainer["GuildSettingsView"]):
    def __init__(self, guild: Guild, game: Game) -> None:
        super().__init__(
            ui.TextDisplay(
                LocaleStr(
                    custom_str="# {title}\n{description}",
                    title=LocaleStr(key="guild_settings.reminder_notification_settings.title"),
                    description=LocaleStr(key="guild_settings.reminder_notification_settings.description"),
                )
            ),
            discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.small),
            discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.small),
            ui.Section(
                ui.TextDisplay(
                    LocaleStr(
                        custom_str="### {emoji} {description}",
                        emoji=emojis.EVENT,
                        description=LocaleStr(key="guilds.reminders_module.edit.stream_reminder.description"),
                    )
                ),
                accessory=StreamReminderToggle(current_toggle=guild.reminders[game].stream_reminder),
            )
        )