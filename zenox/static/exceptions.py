from __future__ import annotations

from ..l10n import LocaleStr
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zenox.static.enums import Game


class ZenoxException(Exception):
    def __init__(self, title: LocaleStr, message: LocaleStr | None = None):
        self.title = title
        self.message = message

class InvalidInputError(ZenoxException):
    def __init__(self, reason: LocaleStr):
        super().__init__(title=LocaleStr(key="invalid_input_error_title"), message=reason)

class WikiCodesHeaderMismatchError(ZenoxException):
    def __init__(self):
        super().__init__("Mismatching Wiki Codes Header")

class WikiCodesDataMismatchError(ZenoxException):
    def __init__(self, reason: str):
        super().__init__("Mismatching Wiki Codes Data", reason)

class HoyolabAPIError(ZenoxException):
    def __init__(self):
        super().__init__(title=LocaleStr(key="hoyolab_api_error_title"), message=LocaleStr(key="hoyolab_api_error_message"))
    
class EnkaAPIError(ZenoxException):
    def __init__(self, status_code: int):
        super().__init__(title=LocaleStr(key="enka_api_error_title"), message=LocaleStr(key="enka_api_error_message", status_code=status_code))

class NoAccountsFoundError(ZenoxException):
    def __init__(self, games: tuple[Game]):
        super().__init__(
            title=LocaleStr(key="no_accounts_found_error_title"),
            message=LocaleStr(key="no_accounts_found_error_message", games=", ".join(game.value for game in games))
        )