from .l10n import LocaleStr


class ZenoxException(Exception):
    def __init__(self, title: LocaleStr, message: LocaleStr):
        self.title = title
        self.message = message


class InvalidInputError(ZenoxException):
    def __init__(self, message: LocaleStr):
        super().__init__(title=LocaleStr(key="invalid_input.title"), message=message)


class EnkaAPIError(ZenoxException):
    def __init__(self, status_code: int | None = None) -> None:
        desc = LocaleStr(key="enka_api_error.description", status_code=status_code or "?")
        super().__init__(title=LocaleStr(key="enka_api_error.title"), message=desc)
        self.status_code = status_code


class HoyolabAPIError(ZenoxException):
    def __init__(self, retcode: int | None = None) -> None:
        desc = LocaleStr(key="hoyolab_api_error.description", retcode=retcode or "?")
        super().__init__(title=LocaleStr(key="hoyolab_api_error.title"), message=desc)
        self.retcode = retcode


class HoyolabLoginError(ZenoxException):
    def __init__(self, retcode: int | None = None) -> None:
        desc = LocaleStr(key="hoyolab_login_error.description", retcode=retcode or "?")
        super().__init__(title=LocaleStr(key="hoyolab_login_error.title"), message=desc)
        self.retcode = retcode
