from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from zenox import emojis, ui
from zenox.db.classes import Guild
from zenox.constants import ZENOX_LOCALES
from zenox.l10n import LocaleStr

if TYPE_CHECKING:
    from zenox.types import Interaction

    from ..view import GuildSettingsView # noqa: F401

class LanguageSelector(ui.Select["GuildSettingsView"]):
    def __init__(self, current_locale: discord.Locale) -> None:
        super().__init__(
            options=[
                ui.SelectOption(
                    label=ZENOX_LOCALES[locale]["name"],
                    value=locale.value,
                    emoji=ZENOX_LOCALES[locale]["emoji"],
                    default=locale == current_locale,
                )
                for locale in ZENOX_LOCALES
            ]
        )

    async def callback(self, i: Interaction) -> None:
        self.view.locale = discord.Locale(self.values[0])

        await self.view.guild._update_language(self.view.locale)
        
        await self.view.update(i)

class GuildSettingsContainer(ui.DefaultContainer["GuildSettingsView"]):
    def __init__(self, guild: Guild) -> None:
        super().__init__(
            ui.TextDisplay(
                LocaleStr(
                    custom_str="# {title}\n{description}",
                    title=LocaleStr(key="guild_settings.title"),
                    description=LocaleStr(key="guild_settings.description"),
                )
            ),
            discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.small),
            ui.TextDisplay(
                LocaleStr(
                    custom_str="### {emoji} {description}",
                    emoji=emojis.LANGUAGE,
                    description=LocaleStr(key="guild_settings.language_description"),
                )
            ),
            discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.small),
            ui.ActionRow(LanguageSelector(guild.language)),
        )