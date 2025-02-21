import discord
from typing import TYPE_CHECKING
from ...components import ToggleButton
from zenox.l10n import LocaleStr
from zenox.db.structures import CodesConfig

if TYPE_CHECKING:
    from ..view import GuildSettingsUI

class StreamRedemptionCodeToggle(ToggleButton["GuildSettingsUI"]):
    def __init__(self, current_toggle: bool) -> None:
        super().__init__(
            current_toggle,
            LocaleStr(key="stream_redemption_codes.label"),
            row=2
        )
    
    async def callback(self, interaction: discord.Interaction):
        await super().callback(interaction)
        self.view.save_setting(CodesConfig, "stream_codes", self.current_toggle)
        await self.view.update_ui(interaction)

class AllRedemptionCodesToggle(ToggleButton["GuildSettingsUI"]):
    def __init__(self, current_toggle: bool) -> None:
        super().__init__(
            current_toggle,
            LocaleStr(key="all_redemption_codes.label"),
            row=2
        )
    
    async def callback(self, interaction: discord.Interaction):
        await super().callback(interaction)
        self.view.save_setting(CodesConfig, "all_codes", self.current_toggle)
        await self.view.update_ui(interaction)