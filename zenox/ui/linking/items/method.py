import discord
from typing import TYPE_CHECKING, Any
from zenox.l10n import LocaleStr
from zenox.static.embeds import DefaultEmbed
from ...components import Select, SelectOption
from .game import GameSelector

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
                    value=method
                )
                for method in ["UID"]
            ]
        )
        return options

    async def callback(self, interaction: discord.Interaction) -> Any:
        selected = self.values[0]
        self.view.method = selected
        
        if self.view.method == "UID":
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