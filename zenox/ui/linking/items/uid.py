from __future__ import annotations

from ...components import Label, Modal, TextInput
from zenox.l10n import LocaleStr

__all__ = ("EnkaUsernameModal",)


class EnkaUsernameModal(Modal):
    username_input: Label[TextInput] = Label(
        text=LocaleStr(key="linking.enka_modal.username.label"),
        component=TextInput(
            placeholder=LocaleStr(key="linking.enka_modal.username.placeholder"),
            min_length=3,
            max_length=24,
        ),
    )

    def __init__(self) -> None:
        super().__init__(title=LocaleStr(key="linking.enka_modal.title"))
