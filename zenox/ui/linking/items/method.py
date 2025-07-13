import discord
from typing import TYPE_CHECKING, Any
from zenox.l10n import LocaleStr
from zenox.static.embeds import DefaultEmbed
from ...components import Select, SelectOption
from .game import GameSelector
from .uid import UIDInput

if TYPE_CHECKING:
    from ..view import LinkingUI


class MethodSelector(Select["LinkingUI"]):
    def __init__(self) -> None:
        options = self._get_options()
        super().__init__(options=options, placeholder=LocaleStr(key="linking_method_select.placeholder"))

    @staticmethod
    def _get_options() -> list[SelectOption]:
        options: list[SelectOption] = []
        options.extend(
            [
                SelectOption(
                    label=method,
                    value=method,
                    description=LocaleStr(key=f"linking_method_select.description.{method.lower()}"),
                )
                for method in ["Hoyolab", "UID"]
            ]
        )
        return options

    async def callback(self, interaction: discord.Interaction) -> Any:
        selected = self.values[0]
        
        if selected == "Hoyolab":
            modal = UIDInput(min_length=7, max_length=10)
            modal.translate(self.view.locale)
            await interaction.response.send_modal(modal)
            await modal.wait()
            if modal.incomplete:
                return
            uid = modal.uid_input.value
            await self.view.hoyolab_linking(uid, interaction)

        elif selected == "UID":
            if len(self.view._user.accounts) >= 10:
                embed = DefaultEmbed(
                    locale=self.view.locale,
                    title=LocaleStr(key="linking_embed_title.error"),
                    description=LocaleStr(key="linking_embed_description.max_accounts_reached")
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            embed = DefaultEmbed(
                locale=self.view.locale,
                title=LocaleStr(key="linking_embed_title.game"),
                description=LocaleStr(key="linking_embed_description.game")
            )

            self.view.clear_items()
            self.view.add_item(GameSelector())

            await interaction.response.edit_message(
                embed=embed,
                view=self.view
            )