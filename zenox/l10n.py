import pathlib
import contextlib
from pathlib import Path
import os
import yaml
import discord
from discord import app_commands
from typing import Self, Any
from loguru import logger
from .static.constants import ZENOX_LOCALES

from discord.enums import Locale

L10N_PATH = pathlib.Path("./zenox/l10n")
SUPPORTED_LANG = [x.value for x in ZENOX_LOCALES]

class LocaleStr:
    def __init__(
        self,
        *,
        key: str | None = None,
        custom_str: str | None = None,
        translate: bool = True,
        **kwargs
    ) -> None:
        self.key = key
        self.custom_str = custom_str
        self.extras: dict[str, Any] = kwargs
    
    def translate(self, locale: Locale) -> str:
        return translator.translate(self, locale)

class Translator:
    def __init__(self) -> None:
        self._localizations: dict[str, dict[str, str]] = {}
        self.load_l10n_files()
        pass
    def load_l10n_files(self) -> None:
        for filepath in L10N_PATH.glob("*.yaml"):
            if not filepath.exists():
                continue
            lang = filepath.stem
            self._localizations[lang] = self.read_yaml(filepath.as_posix())
    def read_yaml(self, filepath: Path) -> None:
        with open(filepath, 'r', encoding='utf-8') as f:
            yaml_data = yaml.safe_load(f)
        localizations = {}
        for locale, strings in yaml_data.items():
            localizations[locale] = strings
        return localizations
    def _translate_extras(self, extras: dict[str, Any], locale: Locale) -> dict[str, Any]:
        extras_: dict[str, Any] = {}
        for k, v in extras.items():
            if isinstance(v, LocaleStr):
                extras_[k] = self.translate(v, locale)
            elif isinstance(v, list) and isinstance(v[0], LocaleStr):
                extras_[k] = "/".join([self.translate(i, locale) for i in v])
            else:
                extras_[k] = v
        return extras_
    def translate(self, string: LocaleStr | str, locale: Locale):
        if (isinstance(string, str)):
            return string
        extras = self._translate_extras(string.extras, locale)

        if string.key:
            if locale.value not in SUPPORTED_LANG: # Language not supported
                translation = self._localizations["en-US"].get(string.key)
            else:
                translation = self._localizations[locale.value].get(string.key)
        elif string.custom_str:
            translation = string.custom_str
        
        if not translation: # Can be None if the String hasn't been translated to the Locale
            translation = self._localizations["en-US"].get(string.key) # Wil never be None

        with contextlib.suppress(KeyError):
            translation = translation.format(**extras)
        return translation

class AppCommandTranslator(app_commands.Translator):
    def __init__(self) -> None:
        super().__init__()

    async def translate(
        self,
        string: app_commands.locale_str,
        locale: discord.Locale,
        context: app_commands.TranslationContext,
    ) -> str:
        if (key := string.extras.get("key")) is None:
            return string.message
        return translator.translate(LocaleStr(key=key), locale)
    
translator = Translator()