import discord
from ..components import View, Button, Modal, TextInput, GoBackButton
from discord import User, Member
from discord import Locale
from zenox.db.structures import SpecialProgram, GuildConfig, Game, DB, CodesConfig
from zenox.l10n import Translator, LocaleStr
from zenox.static import emojis
from zenox.bot.bot import Zenox
from zenox.static.utils import path_to_bytesio
from .items.primaryOptions import updateImage, publishButton, publishGuildButton, publishDevGuildButton
from .items.confirmPublish import confirmButton
from typing import Literal

class HoyolabCodesUI(View):
    def __init__(
            self,
            *,
            author: User | Member,
            locale: Locale,
            data: SpecialProgram
    ):
        super().__init__(author=author, locale=locale)

        self.add_item(updateImage())
        self.add_item(publishButton(disabled=data.published or not data.found))
        self.add_item(publishGuildButton())
        self.add_item(publishDevGuildButton())
        
        self.data: SpecialProgram = data
        self.action: Literal["Global", "Guild", "Dev"] | None = None
        self.guild_id: int | None = None
    
    async def rebuild_ui(self, interaction: discord.Interaction, menu: str, *, row: int = 4, back_button: bool = True):
        # BUG: Channelselect dissappearing when going back
        go_back_button = GoBackButton(self.children, self.get_embeds(interaction.message), None, row=row)
        self.clear_items()

        match menu:
            case 'main':
                self.add_item(updateImage())
                self.add_item(publishButton(disabled=self.data.published or not self.data.found))
                self.add_item(publishGuildButton())
                self.add_item(publishDevGuildButton())

                self.action = None
                self.guild_id = None
            case 'publish':
                self.add_item(confirmButton())
        
        if back_button:
            self.add_item(go_back_button)
        if not interaction.response.is_done():
            await interaction.response.edit_message(view=self)
        else:
            await interaction.followup.edit_message(message_id=interaction.message.id, view=self)
    async def update_embed(self, interaction: discord.Interaction):
        _, embed, _ = await self.data.buildMessage(interaction.client, self.locale)
        await self.absolute_edit(interaction, embed=embed)
    
    async def update_ui(self, interaction: discord.Interaction):
        await self.absolute_edit(interaction, view=self)