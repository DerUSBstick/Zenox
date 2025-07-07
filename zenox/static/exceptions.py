from ..l10n import LocaleStr

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