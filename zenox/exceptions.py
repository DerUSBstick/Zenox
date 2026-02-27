from .l10n import LocaleStr


class ZenoxException(Exception):
    def __init__(self, title: LocaleStr, message: LocaleStr):
        self.title = title
        self.message = message


class InvalidInputError(ZenoxException):
    def __init__(self, message: LocaleStr):
        super().__init__(title=LocaleStr(key="invalid_input.title"), message=message)
