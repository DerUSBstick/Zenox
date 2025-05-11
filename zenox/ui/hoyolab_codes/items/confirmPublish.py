import discord
from typing import TYPE_CHECKING
from ...components import View, Button, Modal, TextInput, GoBackButton
from discord import User, Member
from discord import Locale
from zenox.db.mongodb import DB, ANALYTICSDB
from zenox.db.structures import SpecialProgram, GuildConfig, Game, CodesConfig
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
            _success, _failed, _forbidden, _no_channel, _no_role = await self.publishSpecialProgramCodes(interaction.client)
        elif self.view.action == 'Guild' or self.view.action == 'Dev':
            res = await self.publishToGuild(interaction.client, self.view.guild_id)
        else:
            raise ValueError("Invalid action")
        self.view.data.mark("published")
        for code in self.view.data.codes:
            code._update_val("published", True)
        
        if self.view.action in ['Guild', 'Dev']:
            await interaction.followup.send("Successfully published codes to Guild" if res else "Failed to publish codes to Guild")
        else:
            await interaction.followup.send(f"Successfully published codes to {_success} guilds\nFailed to publish codes to {_failed} guilds\nFailed to publish to {_forbidden} guilds due to missing permissions\nFailed to publish to {_no_channel} guilds due to missing channels\nMissing role in {_no_role} guilds")
            ANALYTICSDB.hoyolab_codes.insert_one({
                "type": "publish",
                "game": self.view.data.game,
                "version": self.view.data.version,
                "stats": {
                    "success": _success,
                    "failed": _failed,
                    "forbidden": _forbidden,
                    "no_channel": _no_channel,
                    "no_role": _no_role
                }
            })

        await self.view.rebuild_ui(interaction, menu="main", back_button=False)
    
    def _pre_translate(self):
        raise NotImplementedError

    async def publishToGuild(self, client: Zenox, guild_id: int) -> bool:
        # Only used for publishing to a single guild
        try:
            role = None 
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

    async def publishSpecialProgramCodes(self, client: Zenox) ->  tuple[int, int, int, int, int]:
        _success, _failed, _forbidden, _no_channel, _no_role = 0, 0, 0, 0, 0
        guilds = [guild["id"] for guild in DB.guilds.find({})]

        for guild in guilds:
            try:
                role = None
                guild = GuildConfig(guild)
                guildObject = client.get_guild(guild.id)
                LANG = guild.language
                if not guild.codes_config[self.view.data.game].channel:
                    _no_channel += 1
                    continue
                CHANNEL = guildObject.get_channel(guild.codes_config[self.view.data.game].channel)
                if not CHANNEL:
                    guild.updateGameConfigValue(self.view.data.game, CodesConfig, "channel", None)
                    continue
                warning = None
                if guild.codes_config[self.view.data.game].role_ping:
                    role = guildObject.get_role(guild.codes_config[self.view.data.game].role_ping)
                    if not role:
                        _no_role += 1
                        warning = LocaleStr(key="role_not_found_error").translate(LANG)
                        guild.updateGameConfigValue(self.view.data.game, CodesConfig, "role_ping", None)
                new_codes = LocaleStr(key="wikicodes_embed.title").translate(LANG)
                content = f"{emojis.ANNOUNCEMENT} {'@everyone' if guild.codes_config[self.view.data.game].everyone_ping else ''} {role.mention if role else ''} **{new_codes}** {warning if warning else ''}"
                view, embed, files = await self.view.data.buildMessage(client, LANG)

                await CHANNEL.send(content=content, embed=embed, view=view, files=files)
                _success += 1
            except (discord.Forbidden, AttributeError):
                guild.updateGameConfigValue(self.view.data.game, CodesConfig, "channel", None)
                _forbidden += 1
            except Exception as e:
                client.capture_exception(e)
                _failed += 1
        return _success, _failed, _forbidden, _no_channel, _no_role