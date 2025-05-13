import discord
from typing import TYPE_CHECKING
from ...components import View, Button, Modal, TextInput, GoBackButton
from discord import User, Member
from discord import Locale
from zenox.db.structures import SpecialProgram, GuildConfig, Game, DB, CodesConfig
from zenox.l10n import Translator, LocaleStr
from zenox.static import emojis
from zenox.bot.bot import Zenox
from zenox.static.utils import path_to_bytesio

if TYPE_CHECKING:
    from ..view import HoyolabCodesUI

class imageUrlModal(Modal):
    image_url = TextInput(label="Image URL", style=discord.TextStyle.short)

class guildIdModal(Modal):
    guild_id = TextInput(label="Guild ID", style=discord.TextStyle.short, placeholder="Guild ID", is_digit=True)

class publishButton(Button["HoyolabCodesUI"]):
    def __init__(self, disabled: bool):
        super().__init__(label="Publish", disabled=disabled, style=discord.ButtonStyle.danger)
    
    async def callback(self, interaction):
        self.view.action = "Global"
        await self.view.rebuild_ui(interaction, menu="publish")

class publishGuildButton(Button["HoyolabCodesUI"]):
    def __init__(self):
        super().__init__(label="Publish to Guild", style=discord.ButtonStyle.primary)
    
    async def callback(self, interaction):
        self.view.action = "Guild"
        guild_id_modal = guildIdModal(title="Enter Guild ID")
        await interaction.response.send_modal(guild_id_modal)
        await guild_id_modal.wait()
        incomplete = guild_id_modal.incomplete
        if incomplete:
            return
        self.view.guild_id = int(guild_id_modal.guild_id.value)
        await self.view.rebuild_ui(interaction, menu="publish")

class publishDevGuildButton(Button["HoyolabCodesUI"]):
    def __init__(self):
        super().__init__(label="Publish to Dev Guild", style=discord.ButtonStyle.primary)
    
    async def callback(self, interaction):
        self.view.action = "Dev"
        self.view.guild_id = 1129777497454686330

        await self.view.rebuild_ui(interaction, menu="publish")

class updateImage(Button["HoyolabCodesUI"]):
    def __init__(self):
        super().__init__(label="Update Image", style=discord.ButtonStyle.primary)
    
    async def callback(self, interaction):
        image_modal = imageUrlModal(title="Update Image URL")
        await interaction.response.send_modal(image_modal)
        await image_modal.wait()
        incomplete = image_modal.incomplete
        if incomplete:
            return
        
        self.view.data.updateImage(image_modal.image_url.value)
        await self.view.update_embed(interaction)