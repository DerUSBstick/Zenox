from __future__ import annotations

import discord
from typing import TYPE_CHECKING

from ...components import ChannelSelect, RoleSelect, ToggleButton, Button
from zenox.embeds import DefaultEmbed
from zenox.l10n import LocaleStr

if TYPE_CHECKING:  #
    from ..view import GuildSettingsUI  # noqa: F401
    from ....types import Interaction


class ChannelSelector(ChannelSelect["GuildSettingsUI"]):
    def __init__(self):
        super().__init__(
            channel_type=[discord.ChannelType.text, discord.ChannelType.news],
            placeholder=LocaleStr(key="guilds.codes_module.edit.channel.placeholder"),
            min_values=1,
            max_values=1,
        )

    async def callback(self, i: Interaction):
        assert self.view.game is not None

        await self.view.guild._update_module_setting(
            module_name="codes",
            game=self.view.game,
            setting="channel",
            value=self.values[0].id if self.values else None,
        )
        await self.view.update_ui(i)


class RoleSelector(RoleSelect["GuildSettingsUI"]):
    def __init__(self):
        super().__init__(
            placeholder=LocaleStr(
                key="guilds.codes_module.edit.mention_role.placeholder"
            ),
            min_values=0,
            max_values=1,
        )

    async def callback(self, i: Interaction):
        assert self.view.game is not None

        await self.view.guild._update_module_setting(
            module_name="codes",
            game=self.view.game,
            setting="mention_role",
            value=self.values[0].id if self.values else None,
        )
        await self.view.update_ui(i)


class MentionEveryoneToggle(ToggleButton["GuildSettingsUI"]):
    def __init__(self, current_toggle: bool):
        super().__init__(
            current_toggle=current_toggle,
            toggle_label=LocaleStr(
                key="guilds.codes_module.edit.mention_everyone.label"
            ),
        )

    async def callback(self, i: Interaction):
        assert self.view.game is not None

        await super().callback(i)

        await self.view.guild._update_module_setting(
            module_name="codes",
            game=self.view.game,
            setting="mention_everyone",
            value=self.current_toggle,
        )
        await self.view.update_ui(i)


class PremiumOnlyToggle(ToggleButton["GuildSettingsUI"]):
    def __init__(self, current_toggle: bool):
        super().__init__(
            current_toggle=current_toggle,
            toggle_label=LocaleStr(
                key="guilds.codes_module.edit.ping_premium_only.label"
            ),
        )

    async def callback(self, i: Interaction):
        assert self.view.game is not None

        await super().callback(i)

        await self.view.guild._update_module_setting(
            module_name="codes",
            game=self.view.game,
            setting="ping_premium_only",
            value=self.current_toggle,
        )
        await self.view.update_ui(i)


class CodesHelpButton(Button["GuildSettingsUI"]):
    def __init__(self):
        super().__init__(emoji="❓", style=discord.ButtonStyle.secondary)

    async def callback(self, i: Interaction):
        embed = DefaultEmbed(
            locale=self.view.locale,
            title=LocaleStr(key="guilds.codes_module.help.title"),
            description=LocaleStr(key="guilds.codes_module.help.description"),
        )
        embed.add_field(
            name=LocaleStr(key="guilds.codes_module.help.channel.title"),
            value=LocaleStr(key="guilds.codes_module.help.channel.description"),
            inline=False,
        )
        embed.add_field(
            name=LocaleStr(key="guilds.codes_module.help.mention_everyone.title"),
            value=LocaleStr(
                key="guilds.codes_module.help.mention_everyone.description"
            ),
            inline=False,
        )
        embed.add_field(
            name=LocaleStr(key="guilds.codes_module.help.mention_role.title"),
            value=LocaleStr(key="guilds.codes_module.help.mention_role.description"),
            inline=False,
        )
        embed.add_field(
            name=LocaleStr(key="guilds.codes_module.help.ping_premium_only.title"),
            value=LocaleStr(
                key="guilds.codes_module.help.ping_premium_only.description"
            ),
            inline=False,
        )

        await i.response.send_message(embed=embed, ephemeral=True)
