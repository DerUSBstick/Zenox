from __future__ import annotations

import discord

from typing import TYPE_CHECKING
from enum import StrEnum

from zenox import ui
from zenox.db.classes import Guild
from zenox.enums import Game
from zenox.constants import CODES_CONFIG_NOT_SUPPORTED, REMINDERS_CONFIG_NOT_SUPPORTED, YOUTUBE_NOTIFICATIONS_CONFIG_NOT_SUPPORTED
from zenox.emojis import get_game_emoji
from zenox.l10n import LocaleStr

from .containers import (
    GuildSettingsContainer,
    CodeNotificationSettingsContainer,
    ReminderNotificationSettingsContainer,
    YTNotificationSettingsContainer,
)

if TYPE_CHECKING:
    from zenox.types import Interaction, User

class GuildSettingsCategory(StrEnum):
    GUILD_SETTINGS = "guild_settings"
    CODE_NOTIFICATION_SETTINGS = "code_notification_settings"
    REMINDER_NOTIFICATION_SETTINGS = "reminder_notification_settings"
    YT_NOTIFICATION_SETTINGS = "yt_notification_settings"

GAME_SELECT_CATEGORIES: set[GuildSettingsCategory] = {
    GuildSettingsCategory.CODE_NOTIFICATION_SETTINGS,
    GuildSettingsCategory.REMINDER_NOTIFICATION_SETTINGS,
    GuildSettingsCategory.YT_NOTIFICATION_SETTINGS,
}

class CategorySelector(ui.Select["GuildSettingsView"]):
    def __init__(self, current_category: GuildSettingsCategory) -> None:
        super().__init__(
            options=[
                ui.SelectOption(
                    label=LocaleStr(key=category.value),
                    value=category.value,
                    default=category == current_category,
                )
                for category in GuildSettingsCategory
            ]
        )
    
    async def callback(self, i: Interaction) -> None:
        self.view.category = GuildSettingsCategory(self.values[0])
        await self.view.update(i)

class GameSelector(ui.Select["GuildSettingsView"]):
    def __init__(self, current_game: Game, skip_games: list[Game]) -> None:
        super().__init__(
            options=[
                ui.SelectOption(
                    label=game.value,
                    value=game.value,
                    emoji=get_game_emoji(game),
                    default=game == current_game,
                )
                for game in Game
                if game not in skip_games
            ],
            placeholder=LocaleStr(key="guilds.select_game"),
            min_values=1,
            max_values=1,
        )

    async def callback(self, i: Interaction) -> None:
        self.view.game = Game(self.values[0])
        await self.view.update(i) 


class GuildSettingsView(ui.LayoutView):
    def __init__(self, *, author: User, locale: discord.Locale, guild: Guild):
        super().__init__(author=author, locale=locale)

        self.category = GuildSettingsCategory.GUILD_SETTINGS

        self.guild = guild
        self.game: Game = Game.GENSHIN
    
    async def _get_container(self) -> ui.Container:
        if self.category == GuildSettingsCategory.GUILD_SETTINGS:
            return GuildSettingsContainer(guild=self.guild)
        
        if self.category == GuildSettingsCategory.CODE_NOTIFICATION_SETTINGS:
            return CodeNotificationSettingsContainer(guild=self.guild, game=self.game)
        
        if self.category == GuildSettingsCategory.REMINDER_NOTIFICATION_SETTINGS:
            return ReminderNotificationSettingsContainer(guild=self.guild, game=self.game)
        
        if self.category == GuildSettingsCategory.YT_NOTIFICATION_SETTINGS:
            return YTNotificationSettingsContainer(guild=self.guild, game=self.game)

        raise ValueError(f"Invalid category: {self.category}")

    async def update(self, i: Interaction) -> None:
        if not i.response.is_done():
            await i.response.defer()
        
        container = await self._get_container()
        container.add_item(discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small))

        if self.category in GAME_SELECT_CATEGORIES:
            if self.category == GuildSettingsCategory.CODE_NOTIFICATION_SETTINGS:
                skip = CODES_CONFIG_NOT_SUPPORTED
            elif self.category == GuildSettingsCategory.REMINDER_NOTIFICATION_SETTINGS:
                skip = REMINDERS_CONFIG_NOT_SUPPORTED
            elif self.category == GuildSettingsCategory.YT_NOTIFICATION_SETTINGS:
                skip = YOUTUBE_NOTIFICATIONS_CONFIG_NOT_SUPPORTED
            else:
                skip = []

            container.add_item(ui.ActionRow(GameSelector(current_game=self.game, skip_games=skip)))
            container.add_item(discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small))
        
        container.add_item(ui.ActionRow(CategorySelector(current_category=self.category)))

        self.clear_items()
        self.add_item(container)

        self.message = await i.edit_original_response(view=self)