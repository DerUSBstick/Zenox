from __future__ import annotations

import discord
import pathlib
from typing import TYPE_CHECKING

from ..components import View, Select, SelectOption
from ...db.classes import UserConfig
from ...constants import ZENOX_LOCALES
from ...embeds import DefaultEmbed
if TYPE_CHECKING:
    from ...types import Interaction, User


class UserSettingsUI(View):
    def __init__(self, *, author: User, locale: discord.Locale, user: UserConfig):
        super().__init__(author=author, locale=locale)
        self.user = user

        self.add_item(LanguageSelector(current_locale=locale))

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
        filename = self.get_brand_image_filename("DARK", self.locale)
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


class LanguageSelector(Select["UserSettingsUI"]):
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
        await self.view.user._update_language(self.view.locale)
        self.options = self._get_options(self.view.locale)
        await self.view.update_ui(i, translate=True)
