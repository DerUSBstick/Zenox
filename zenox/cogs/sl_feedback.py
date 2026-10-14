from __future__ import annotations

import discord
from discord import app_commands
from discord.app_commands import locale_str
from discord.ext import commands
from typing import TYPE_CHECKING

from zenox.embeds import DefaultEmbed
from zenox.ui.components import Label, Modal, Select, SelectOption, TextInput

if TYPE_CHECKING:
    from ..bot import Zenox
    from ..types import Interaction

FEEDBACK_GUILD_ID = 677642894479327233

CATEGORIES = (
    "Incorrect leaderboard data",
    "Missing character / light cone / build",
    "Rankings or scoring issue",
    "Display / UI issue",
    "Feature request",
    "Other",
)


class SeelelandFeedbackModal(Modal):
    category: Label[Select] = Label(
        text="Category",
        component=Select(options=[SelectOption(label=c, value=c) for c in CATEGORIES], required=True),
    )
    context: Label[TextInput] = Label(
        text="Character / leaderboard (optional)",
        description="e.g. Firefly, E0S1, Light cone name, or your UID",
        component=TextInput(required=False, max_length=100),
    )
    message: Label[TextInput] = Label(
        text="Your feedback",
        component=TextInput(
            style=discord.TextStyle.paragraph,
            placeholder="What went wrong, or what would you like to see?",
            min_length=5,
            max_length=1500,
        ),
    )

    def __init__(self) -> None:
        super().__init__(title="Seeleland Feedback")


class SeelelandFeedback(commands.Cog):
    def __init__(self, client: Zenox):
        self.client = client

    @app_commands.command(
        name=locale_str("sl_feedback"),
        description=locale_str("Send feedback about the Seeleland integration"),
    )
    @app_commands.checks.cooldown(1, 60, key=lambda i: i.user.id)
    @app_commands.user_install()
    @app_commands.guild_install()
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def sl_feedback_command(self, interaction: Interaction) -> None:
        if interaction.guild_id != FEEDBACK_GUILD_ID:
            await interaction.response.send_message("This command isn't available here.", ephemeral=True)
            return

        channel_id = self.client.config.seeleland_feedback_channel_id
        if channel_id is None:
            await interaction.response.send_message("Feedback is currently unavailable.", ephemeral=True)
            return

        modal = SeelelandFeedbackModal()
        modal.translate(interaction.locale)
        await interaction.response.send_modal(modal)
        if await modal.wait():
            return

        category = modal.category.component.values[0]
        embed = DefaultEmbed(
            discord.Locale.american_english,
            title=f"Seeleland Feedback: {category}",
            description=modal.message.component.value,
        )
        embed.set_author(name=f"{interaction.user} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
        context = modal.context.component.value.strip()
        if context:
            embed.add_field(name="Context", value=context, inline=False)
        if interaction.guild_id:
            embed.set_footer(text=f"Guild: {interaction.guild_id}")

        channel = self.client.get_channel(channel_id) or await self.client.fetch_channel(channel_id)
        if not isinstance(channel, discord.abc.Messageable):
            await interaction.followup.send("Feedback is currently unavailable.", ephemeral=True)
            return
        await channel.send(embed=embed)

        await interaction.followup.send("Thanks, your feedback has been sent.", ephemeral=True)


async def setup(client: Zenox) -> None:
    await client.add_cog(SeelelandFeedback(client))
