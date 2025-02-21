import discord
from discord.utils import MISSING
from zenox.l10n import LocaleStr
from zenox.db.structures import CodesConfig
from typing import TYPE_CHECKING
from ...components import RoleSelect, ToggleButton

if TYPE_CHECKING:
    from ..view import GuildSettingsUI

class PingRoleSelect(RoleSelect["GuildSettingsUI"]):
    def __init__(self, role: int | None):
        super().__init__(
            row=1,
            placeholder=LocaleStr(key="role_select.placeholder"),
            default_values=[discord.SelectDefaultValue(id=role, type=discord.SelectDefaultValueType.role)] if role != None else [],
            min_values=0,
            max_values=1
        )
    
    async def callback(self, interaction: discord.Interaction):
        if self.values:
            selected: discord.Role = self.values[0]

        self.view.save_setting(CodesConfig, "role_ping", selected.id if self.values else None)
        await self.view.update_ui(interaction)

class EveryonePingToggle(ToggleButton["GuildSettingsUI"]):
    def __init__(self, current_toggle: bool) -> None:
        super().__init__(
            current_toggle,
            LocaleStr(key="everyone_ping.label"),
            row=2
        )
    
    async def callback(self, interaction: discord.Interaction):
        await super().callback(interaction)
        self.view.save_setting(CodesConfig, "everyone_ping", self.current_toggle)
        await self.view.update_ui(interaction)