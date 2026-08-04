from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from zenox import emojis, ui
from zenox.db.classes import Guild
from zenox.enums import Game
from zenox.l10n import LocaleStr

if TYPE_CHECKING:
    from zenox.types import Interaction

    from ..view import GuildSettingsView # noqa: F401

class YTChannelSelector(ui.ChannelSelect["GuildSettingsView"]):
    def __init__(self, channel: int | None):
        super().__init__(
            default_values=[discord.SelectDefaultValue(id=channel, type=discord.SelectDefaultValueType.channel)] if channel else [],
            channel_type=[discord.ChannelType.text, discord.ChannelType.news, discord.ChannelType.public_thread, discord.ChannelType.private_thread],
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
        await self.view.update(i)


class YTRoleSelector(ui.RoleSelect["GuildSettingsView"]):
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
        await self.view.update(i)


class YTMentionEveryoneToggle(ui.EmojiToggleButton["GuildSettingsView"]):
    def __init__(self, current_toggle: bool):
        super().__init__(
            current=current_toggle,
        )

    async def callback(self, i: Interaction):
        assert self.view.game is not None

        self.current = not self.current
        self.update_style()

        await self.view.guild._update_module_setting(
            module_name="youtube_notifications",
            game=self.view.game,
            setting="mention_everyone",
            value=self.current,
        )
        await self.view.update(i)

class YTNotificationSettingsContainer(ui.DefaultContainer["GuildSettingsView"]):
    def __init__(self, guild: Guild, game: Game) -> None:
        super().__init__(
            ui.TextDisplay(
                LocaleStr(
                    custom_str="# {title}\n{description}",
                    title=LocaleStr(key="guild_settings.yt_notification_settings.title"),
                    description=LocaleStr(key="guild_settings.yt_notification_settings.description"),
                )
            ),
            discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.small),
            ui.ActionRow(YTChannelSelector(channel=guild.youtube_notifications[game].channel)),
            discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.small),
            ui.TextDisplay(
                LocaleStr(
                    custom_str="### {emoji} {description}",
                    emoji=emojis.AT_ICON,
                    description=LocaleStr(key="guild_settings.yt_notification_settings.mention_role_description")
                )
            ),
            discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.small),
            ui.ActionRow(YTRoleSelector(role=guild.youtube_notifications[game].mention_role)),
            discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.small),
            discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.small),
            ui.Section(
                ui.TextDisplay(
                    LocaleStr(
                        custom_str="### {emoji} {description}",
                        emoji=emojis.NEWS_CHANNEL,
                        description=LocaleStr(key="guild_settings.yt_notification_settings.mention_everyone_description")
                    )
                ),
                accessory=YTMentionEveryoneToggle(current_toggle=guild.youtube_notifications[game].mention_everyone),
            ),
        )