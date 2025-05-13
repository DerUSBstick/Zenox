import discord
from typing import TYPE_CHECKING, Any
from discord.utils import MISSING
from ...components import ChannelSelect, RoleSelect, ToggleButton, Button, Modal, TextInput
from zenox.l10n import LocaleStr
from zenox.db.structures import CodesConfig, EventReminderConfig, SpecialProgram

if TYPE_CHECKING:
    from ..view import GuildSettingsUI

class ConfigChannelSelect(ChannelSelect["GuildSettingsUI"]):
    def __init__(self, channel: int | None, *, disabled: bool = False, custom_id: str = MISSING):
        super().__init__(
            row=0,
            placeholder=LocaleStr(key="channel_select.placeholder"),
            channel_type=[discord.ChannelType.text, discord.ChannelType.news],
            default_values=[discord.SelectDefaultValue(id=channel, type=discord.SelectDefaultValueType.channel)] if channel != None else [],
            min_values=0,
            disabled=disabled,
            custom_id=custom_id
        )
    
    async def callback(self, interaction: discord.Interaction):
        if self.values:
            selected: discord.app_commands.models.AppCommandChannel = self.values[0]
        
        self.view.save_setting(CodesConfig, "channel", selected.id if self.values else None)
        self.view.conditioned_ui("GameOptions")
        """On Mobile, we need to Update default value to display Input"""
        self.default_values = [discord.SelectDefaultValue(id=selected.id, type=discord.SelectDefaultValueType.channel)] if self.values else []
        await self.view.update_ui(interaction)

class pingPreferences(Button["GuildSettingsUI"]):
    def __init__(self, *, disabled: bool = False, custom_id: str = MISSING) -> None:
        super().__init__(
            label=LocaleStr(key="ping_preferences_button.label"),
            disabled=disabled,
            custom_id=custom_id,
            row=1
        )
    
    async def callback(self, interaction: discord.Interaction) -> Any:
        await self.view.rebuild_ui(interaction, 'PingPreferences', row=2)
        return

class codePreferences(Button["GuildSettingsUI"]):#
    def __init__(self, *, disabled: bool = False, custom_id: str = MISSING) -> None:
        super().__init__(
            label=LocaleStr(key="code_preferences_button.label"),
            disabled=disabled,
            custom_id=custom_id,
            row=1
        )
    
    async def callback(self, interaction: discord.Interaction) -> Any:
        await self.view.rebuild_ui(interaction, 'CodePreferences', row=2)
        return

class StreamReminderToggle(ToggleButton["GuildSettingsUI"]):
    def __init__(self, current_toggle: bool) -> None:
        super().__init__(current_toggle, LocaleStr(key="stream_reminders.label"), row=3)
    
    async def callback(self, interaction: discord.Interaction):
        await super().callback(interaction)
        self.view.save_setting(EventReminderConfig, "streams", self.current_toggle)
        await self.view.update_ui(interaction)

class TestButton(Button["GuildSettingsUI"]):
    def __init__(self) -> None:
        super().__init__(
            label=LocaleStr(key="embed_preview.label"),
            row=3
        )
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False, thinking=True)
        special_program = SpecialProgram(self.view.game, "Zenox")
        _, embed, attachments = await special_program.buildMessage(interaction.client, self.view.settings.language)
        await interaction.followup.send(embed=embed, files=attachments)