from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...components import Select, SelectOption
from zenox.l10n import LocaleStr
from zenox.config import CONFIG

if TYPE_CHECKING:
    from zenox.types import Interaction
    from ..view import LinkingUI # noqa: F401

__all__ = ("MethodSelector",)


class MethodSelector(Select["LinkingUI"]):
    def __init__(self) -> None:
        options = self._build_options()
        super().__init__(
            options=options,
            placeholder=LocaleStr(key="linking.method.placeholder"),
        )

    @staticmethod
    def _build_options() -> list[SelectOption]:
        options = [
            SelectOption(
                label=LocaleStr(key="linking.method.uid.label"),
                value="UID",
                description=LocaleStr(key="linking.method.uid.description"),
            ),
            SelectOption(
                label=LocaleStr(key="linking.method.enka.label"),
                value="Enka",
                description=LocaleStr(key="linking.method.enka.description"),
            ),
        ]
        if CONFIG.hoyolab_enabled:
            options.append(
                SelectOption(
                    label=LocaleStr(key="linking.method.hoyolab.label"),
                    value="Hoyolab",
                    description=LocaleStr(key="linking.method.hoyolab.description"),
                )
            )
        return options

    async def callback(self, interaction: Interaction) -> Any:
        from .game import GameSelector
        from .uid import HoyolabUIDModal, EnkaUsernameModal
        from zenox.embeds import DefaultEmbed

        selected = self.values[0]

        if selected == "UID":
            embed = DefaultEmbed(
                self.view.locale,
                title=LocaleStr(key="linking.game.embed.title"),
                description=LocaleStr(key="linking.game.embed.description"),
            )
            self.view.clear_items()
            self.view.add_item(GameSelector())
            await interaction.response.edit_message(embed=embed, view=self.view)

        elif selected == "Enka":
            modal = EnkaUsernameModal()
            modal.translate(self.view.locale)
            await interaction.response.send_modal(modal)
            await modal.wait()
            username = modal.username_input.component.value.strip()
            if not username:
                return
            await self.view.enka_linking(username, interaction)

        elif selected == "Hoyolab":
            modal = HoyolabUIDModal()
            modal.translate(self.view.locale)
            await interaction.response.send_modal(modal)
            await modal.wait()
            uid = modal.uid_input.component.value.strip()
            if not uid:
                return
            await self.view.hoyolab_linking(uid, interaction)
