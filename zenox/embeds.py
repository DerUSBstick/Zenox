from __future__ import annotations

import discord
from typing import Self
from .l10n import translator, LocaleStr
from .utils import shorten


class Embed(discord.Embed):
    def __init__(
        self,
        locale: discord.Locale,
        *,
        color: int | None = None,
        title: LocaleStr | str | None = None,
        url: str | None = None,
        description: LocaleStr | str | None = None,
    ):
        translated_title = (
            translator.translate(title, locale)
            if isinstance(title, LocaleStr)
            else title
        )
        if translated_title is not None:
            translated_title = shorten(translated_title, 256)

        translated_description = (
            translator.translate(description, locale)
            if isinstance(description, LocaleStr)
            else description
        )
        if translated_description is not None:
            translated_description = shorten(translated_description, 4096)

        super().__init__(
            color=color,
            title=translated_title,
            url=url,
            description=translated_description,
        )
        self.locale = locale

    def add_field(
        self,
        *,
        name: LocaleStr | str,
        value: LocaleStr | str | None = None,
        inline: bool = True,
    ) -> Self:
        translated_name = translator.translate(name, self.locale)
        translated_value = translator.translate(value, self.locale) if value else ""
        return super().add_field(
            name=shorten(translated_name, 256),
            value=shorten(translated_value, 1024),
            inline=inline,
        )

    def set_author(
        self,
        *,
        name: LocaleStr | str,
        url: str | None = None,
        icon_url: str | None = None,
    ) -> Self:
        translated_name = translator.translate(name, self.locale)
        return super().set_author(
            name=shorten(translated_name, 256), url=url, icon_url=icon_url
        )

    def set_footer(
        self, *, text: LocaleStr | str | None = None, icon_url: str | None = None
    ) -> Self:
        translated_text = translator.translate(text, self.locale) if text else None
        return super().set_footer(text=translated_text, icon_url=icon_url)


class DefaultEmbed(Embed):
    def __init__(
        self,
        locale: discord.Locale,
        *,
        title: LocaleStr | str | None = None,
        url: str | None = None,
        description: LocaleStr | str | None = None,
    ) -> None:
        super().__init__(
            locale, color=0xAF9878, title=title, url=url, description=description
        )


class ErrorEmbed(Embed):
    def __init__(
        self,
        locale: discord.Locale,
        *,
        title: LocaleStr | str | None = None,
        url: str | None = None,
        description: LocaleStr | str | None = None,
    ) -> None:
        super().__init__(
            locale, color=0xE74C3C, title=title, url=url, description=description
        )
