import discord
from typing import TYPE_CHECKING
from ...components import View, Button, Modal, TextInput, GoBackButton
from discord import User, Member
from discord import Locale
from zenox.db.structures import SpecialProgam, GuildConfig, Game, DB, CodesConfig
from zenox.l10n import Translator, LocaleStr
from zenox.static import emojis
from zenox.bot.bot import Zenox
from zenox.static.utils import path_to_bytesio

if TYPE_CHECKING:
    from ..view import HoyolabCodesUI

class confirmButton(Button["HoyolabCodesUI"]):
    def __init__(self):
        super().__init__(label="Confirm", style=discord.ButtonStyle.green)
    
    async def callback(self, interaction):
        self.view.disable_items()
        await interaction.response.edit_message(view=self.view)

        if self.view.action == 'Global':
            _total_post_count, _failed = await self.publishSpecialProgramCodes(interaction.client)
        elif self.view.action == 'Guild' or self.view.action == 'Dev':
            res = await self.publishToGuild(interaction.client, self.view.guild_id)
            _total_post_count = 1 if res else 0
            _failed = 0 if res else 1
        else:
            raise ValueError("Invalid action")
        self.view.data.mark("published")
        for code in self.view.data.codes:
            code._update_val("published", True)
        await interaction.followup.send(f"Successfully published to {_total_post_count} Guilds\nFailed to publish to {_failed} Guilds", ephemeral=True)

        await self.view.rebuild_ui(interaction, menu="main", back_button=False)
    
    def _pre_translate(self):
        raise NotImplementedError

    async def publishToGuild(self, client: Zenox, guild_id: int) -> bool:
        try:
            role = None # FIX: UnboundLocalError: local variable 'role' referenced before assignment
            guild = GuildConfig(guild_id)
            guildObject = client.get_guild(guild.id)
            LANG = guild.language
            if not guild.codes_config[self.view.data.game].channel:
                return False
            CHANNEL = guildObject.get_channel(guild.codes_config[self.view.data.game].channel)
            if not CHANNEL:
                return False
            warning = None
            if guild.codes_config[self.view.data.game].role_ping:
                role = guildObject.get_role(guild.codes_config[self.view.data.game].role_ping)
                if not role:
                    warning = LocaleStr(key="role_not_found_error").translate(LANG)
                    guild.updateGameConfigValue(self.view.data.game, CodesConfig, "role_ping", None)
            new_codes = LocaleStr(key="wikicodes_embed.title").translate(LANG)
            content = f"{emojis.ANNOUNCEMENT} {'@everyone' if guild.codes_config[self.view.data.game].everyone_ping else ''} {role.mention if role else ''} **{new_codes}** {warning if warning else ''}"
            view, embed, files = await self.view.data.buildMessage(client, LANG)

            await CHANNEL.send(content=content, embed=embed, view=view, files=files)
            return True
        except Exception as e:
            client.capture_exception(e)
            return False



    async def publishSpecialProgramCodes(self, client: Zenox) ->  tuple[int, int]:
        _total_post_count: int = 0
        _failed: int = 0
        guilds = [guild["id"] for guild in DB.guilds.find({})]

        for guild in guilds:
            try:
                res = await self.publishToGuild(client, guild)
                if res:
                    _total_post_count += 1
                else:
                    _failed += 1
            except Exception as e:
                client.capture_exception(e)
        return _total_post_count, _failed