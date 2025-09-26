from __future__ import annotations

import discord
import pathlib
from typing import TYPE_CHECKING

from .items.modules import ModuleSelector

from ..components import View, Select, SelectOption, GoBackButton
from ...db.classes import Guild
from ...enums import Game
from ...constants import ZENOX_LOCALES
from ...embeds import DefaultEmbed
from ...emojis import get_game_emoji
from ...utils import path_to_bytesio
from ...l10n import LocaleStr

if TYPE_CHECKING:
    from ...types import Interaction, User


class GuildSettingsUI(View):
    def __init__(self, *, author: User, locale: discord.Locale, guild: Guild):
        super().__init__(author=author, locale=locale)
        self.guild = guild

        self.game: Game | None = None

        self.add_item(LanguageSelector(current_locale=locale))
        self.add_item(GameSelector())

    def get_embed(self) -> DefaultEmbed:
        embed = DefaultEmbed(self.locale)

        embed.set_image(url="attachment://brand.png")
        return embed

    @staticmethod
    def get_brand_image_filename(theme: str, locale: discord.Locale) -> str:
        filename = f"zenox-assets/brand/{theme}-{locale.value}.png"
        if not pathlib.Path(filename).exists():
            return f"zenox-assets/brand/{theme}-en-US.png"
        return filename

    def get_brand_image_file(self) -> discord.File:
        filename = self.get_brand_image_filename("DARK", self.guild.language)
        self.filepath = filename
        return discord.File(filename, filename="brand.png")

    async def update_ui(self, i: Interaction, *, translate: bool = False) -> None:
        if translate:
            self.translate_items()
        await self.absolute_edit(
            i,
            embed=self.get_embed(),
            attachments=[self.get_brand_image_file()],
            view=self,
        )

        if not i.response.is_done():
            await i.response.defer()


class LanguageSelector(Select["GuildSettingsUI"]):
    def __init__(self, current_locale: discord.Locale):
        options = self._get_options(current_locale)
        super().__init__(options=options)

    @staticmethod
    def _get_options(current_locale: discord.Locale) -> list[SelectOption]:
        options: list[SelectOption] = []
        options.extend(
            [
                SelectOption(
                    label=ZENOX_LOCALES[locale]["name"],
                    value=locale.value,
                    emoji=ZENOX_LOCALES[locale]["emoji"],
                    default=locale == current_locale,
                )
                for locale in ZENOX_LOCALES
            ]
        )
        return options

    async def callback(self, i: Interaction):
        selected = self.values[0]
        self.view.locale = discord.Locale(selected)
        await self.view.guild._update_language(self.view.locale)
        self.options = self._get_options(self.view.locale)
        await self.view.update_ui(i, translate=True)


class GameSelector(Select["GuildSettingsUI"]):
    def __init__(self):
        options = self._get_options()
        super().__init__(
            options=options,
            placeholder=LocaleStr(key="guilds.select_game"),
            min_values=1,
            max_values=1,
        )

    @staticmethod
    def _get_options() -> list[SelectOption]:
        options: list[SelectOption] = []
        for game in Game:
            options.append(
                SelectOption(
                    label=game.value,
                    value=game.value,
                    emoji=get_game_emoji(game),
                )
            )
        return options

    async def callback(self, i: Interaction):
        game_value = self.values[0]
        game = Game(game_value)
        self.view.game = game

        go_back_button = GoBackButton(
            self.view.children,
            self.view.get_embeds(i.message),
            path_to_bytesio(self.view.filepath),
        )
        self.view.clear_items()
        self.view.add_item(go_back_button)

        self.view.add_item(ModuleSelector())
        await i.response.edit_message(view=self.view)
