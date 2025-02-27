import discord
import pymongo
from typing import TYPE_CHECKING
from zenox.ui.components import Button, Modal, TextInput
from zenox.l10n import LocaleStr
from zenox.bot.bot import Zenox
from zenox.static.embeds import Embed

if TYPE_CHECKING:
    from ..view import GuildSettingsUI

async def updatePartnerList(client: Zenox):
    _channelID = 1344729244244119653
    _messageID = 1344755025762586738

    embed = Embed(
        locale=discord.Locale.american_english,
        title="Partners Overview",
        color=discord.Color.green()
    )
    
    for partner in client.db.guilds.find({"flags": "PARTNER_GUILD"}, {"partnerData": 1, "_id": 0}).sort("partnerData.guildName", pymongo.ASCENDING):
        if not all(x for x in partner["partnerData"].values()):
            continue
        
        embed.add_field(
            name=partner["partnerData"]["guildName"],
            value=f"{partner['partnerData']['guildDescription']}\n\n[Join Server](https://{partner['partnerData']['inviteUrl']})"
        )

    channel = client.get_channel(_channelID)
    message = channel.get_partial_message(_messageID)
    await message.edit(content=None, embed=embed)
    

class InviteInputModal(Modal):
    invite_input = TextInput(
        label=LocaleStr(key="partner_options.invite_input.label"),
        placeholder="discord.gg/zenoxbot",
        row=0
    )

    def __init__(self, *, title: LocaleStr | str, default: str):
        self.invite_input.default = default
        super().__init__(title=title)

class DescriptionInputModal(Modal):
    description_input = TextInput(
            label=LocaleStr(key="partner_options.description_input.label"),
            placeholder=LocaleStr(key="partner_options.description_input.placeholder"),
            row=0,
            style=discord.TextStyle.short,
            max_length=256
    )

    def __init__(self, *, title: LocaleStr | str, default: str):
        self.description_input.default = default
        super().__init__(title=title)

class SetInviteUrlButton(Button["GuildSettingsUI"]):
    def __init__(self) -> None:
        super().__init__(
            label=LocaleStr(key="partner_options.invite_button.label"),
            style=discord.ButtonStyle.primary,
            row=0
        )
    
    async def callback(self, interaction: discord.Interaction):
        invite_modal = InviteInputModal(title=LocaleStr(key="partner_options.invite_modal.title"), default=self.view.settings.partnerData.inviteUrl)
        invite_modal.translate(self.view.settings.language)
        await interaction.response.send_modal(invite_modal)
        await invite_modal.wait()
        incomplete = invite_modal.incomplete
        if incomplete:
            return
        if self.view.settings.partnerData.guildName != interaction.guild.name:
            self.view.settings.updatePartnerData("guildName", interaction.guild.name)
        gld = await interaction.client.fetch_guild(interaction.guild.id, with_counts=True)
        if self.view.settings.partnerData.guildMemberCount != gld.approximate_member_count:
            self.view.settings.updatePartnerData("guildMemberCount", gld.approximate_member_count)
        self.view.settings.updatePartnerData("inviteUrl", invite_modal.invite_input.value)

        await updatePartnerList(interaction.client)
    
class SetGuildDescriptionButton(Button["GuildSettingsUI"]):
    def __init__(self) -> None:
        super().__init__(
            label=LocaleStr(key="partner_options.description_button.label"),
            style=discord.ButtonStyle.primary,
            row=1
        )
    
    async def callback(self, interaction: discord.Interaction):
        description_modal = DescriptionInputModal(title=LocaleStr(key="partner_options.description_modal.title"), default=self.view.settings.partnerData.guildDescription)
        description_modal.translate(self.view.settings.language)
        await interaction.response.send_modal(description_modal)
        await description_modal.wait()
        incomplete = description_modal.incomplete
        if incomplete:
            return
        if self.view.settings.partnerData.guildName != interaction.guild.name:
            self.view.settings.updatePartnerData("guildName", interaction.guild.name)
        gld = await interaction.client.fetch_guild(interaction.guild.id, with_counts=True)
        if self.view.settings.partnerData.guildMemberCount != gld.approximate_member_count:
            self.view.settings.updatePartnerData("guildMemberCount", gld.approximate_member_count)
        self.view.settings.updatePartnerData("guildDescription", description_modal.description_input.value)

        await updatePartnerList(interaction.client)