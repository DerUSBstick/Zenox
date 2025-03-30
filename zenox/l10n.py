import pathlib
import contextlib
from pathlib import Path
import os
import json, yaml
import discord
from discord import app_commands
from typing import Self, Any
from .static.constants import ZENOX_LOCALES, DatabaseKey, LOCALE_TO_TEXTMAP
from .static.enums import Game

from discord.enums import Locale

SOURCE_LANG = "en-US"
L10N_PATH = pathlib.Path("./zenox/l10n")
SUPPORTED_LANG = [x.value for x in ZENOX_LOCALES]

def gen_string_key(string: str) -> str:
    return string.replace(" ", "_").replace(",", "").replace(".", "").replace("-", "_").lower()

class LocaleStr:
    def __init__(
        self,
        *,
        key: str | None = None,
        custom_str: str | None = None,
        translate: bool = True,
        data_game: Game | None = None,
        **kwargs
    ) -> None:
        self.key = key
        self.custom_str = custom_str
        self.extras: dict[str, Any] = kwargs
        self.translate_ = translate
        self.game = data_game
    
    def translate(self, locale: Locale) -> str:
        return translator.translate(self, locale)

class Translator:
    def __init__(self) -> None:
        self._localizations: dict[str, dict[str, str]] = {}
        self._game_textmaps: dict[Game, dict[str, dict[str, str]]] = {
            game: {} for game in Game
        }
        self.load_l10n_files()
        self.load_text_maps()

    def load_text_maps(self) -> None:
        for game in Game:
            game_str = DatabaseKey[game]
            for locale in ZENOX_LOCALES:
                file_str = LOCALE_TO_TEXTMAP[locale]
                self._game_textmaps[game][locale] = self.read_json(
                    f"zenox/bot/data/text_maps/{game_str}/{file_str}.json"
                )

    def load_l10n_files(self) -> None:
        for filepath in L10N_PATH.glob("*.yaml"):
            if not filepath.exists():
                continue
            lang = filepath.stem
            self._localizations[lang] = self.read_yaml(filepath.as_posix())

    def read_json(self, filepath: str) -> dict[str, str]:
        with open(filepath, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        localizations = {}
        for locale, strings in json_data.items():
            localizations[locale] = strings
        return localizations

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
    
    @staticmethod
    def _get_string_key(string: LocaleStr) -> str:
        if string.key is None:
            if string.custom_str is None:
                raise ValueError("Either key or custom_str must be provided.")
            return gen_string_key(string.custom_str)
        return string.key

    def translate(self, string: LocaleStr | str, locale: Locale):
        if (isinstance(string, str)):
            return string
        
        extras = self._translate_extras(string.extras, locale)
        string_key = self._get_string_key(string)

        if string.game is not None:
            source_string = self._game_textmaps[string.game][discord.Locale(SOURCE_LANG)].get(string_key)

        else:
            source_string = self._localizations[SOURCE_LANG].get(string_key)
        
        if string.translate_ and source_string is None and string.custom_str is None:
            raise ValueError(f"String '{string_key!r}' not found in source language file")
        
        if string.game is not None:
            translation = self._game_textmaps[string.game][locale].get(string_key)
        else:
            translation = self._localizations.get(locale.value, {}).get(string_key)
        
        translation = translation or source_string or string.custom_str or string_key

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