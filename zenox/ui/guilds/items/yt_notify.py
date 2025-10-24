from __future__ import annotations

import discord
from typing import TYPE_CHECKING

from ...components import ChannelSelect, RoleSelect, ToggleButton, Button
from zenox.embeds import DefaultEmbed
from zenox.l10n import LocaleStr

if TYPE_CHECKING:  #
    from ..view import GuildSettingsUI  # noqa: F401
    from ....types import Interaction

class YTChannelSelector(ChannelSelect["GuildSettingsUI"]):
    def __init__(self, channel: int | None):
        super().__init__(
            default_values=[discord.SelectDefaultValue(id=channel, type=discord.SelectDefaultValueType.channel)] if channel else [],
            channel_type=[discord.ChannelType.text, discord.ChannelType.news],
            placeholder=LocaleStr(key="guilds.yt_notify_module.edit.channel.placeholder"),
            min_values=1,
            max_values=1,
        )

    async def callback(self, i: Interaction):
        assert self.view.game is not None

        await self.view.guild._update_module_setting(
            module_name="youtube_notifications",
            game=self.view.game,
            setting="channel",
            value=self.values[0].id if self.values else None,
        )
        await self.view.update_ui(i)


class YTRoleSelector(RoleSelect["GuildSettingsUI"]):
    def __init__(self, role: int | None):
        super().__init__(
            default_values=[discord.SelectDefaultValue(id=role, type=discord.SelectDefaultValueType.role)] if role else [],
            placeholder=LocaleStr(
                key="guilds.yt_notify_module.edit.mention_role.placeholder"
            ),
            min_values=0,
            max_values=1,
        )

    async def callback(self, i: Interaction):
        assert self.view.game is not None

        await self.view.guild._update_module_setting(
            module_name="youtube_notifications",
            game=self.view.game,
            setting="mention_role",
            value=self.values[0].id if self.values else None,
        )
        await self.view.update_ui(i)


class YTMentionEveryoneToggle(ToggleButton["GuildSettingsUI"]):
    def __init__(self, current_toggle: bool):
        super().__init__(
            current_toggle=current_toggle,
            toggle_label=LocaleStr(
                key="guilds.yt_notify_module.edit.mention_everyone.label"
            ),
        )

    async def callback(self, i: Interaction):
        assert self.view.game is not None

        await super().callback(i)

        await self.view.guild._update_module_setting(
            module_name="youtube_notifications",
            game=self.view.game,
            setting="mention_everyone",
            value=self.current_toggle,
        )
        await self.view.update_ui(i)