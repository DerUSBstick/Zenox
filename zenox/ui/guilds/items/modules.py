from __future__ import annotations

from typing import TYPE_CHECKING
from ...components import Select, SelectOption, GoBackButton
from ....l10n import LocaleStr
from ....utils import path_to_bytesio
from .codes import (
    ChannelSelector,
    RoleSelector,
    MentionEveryoneToggle,
    CodesHelpButton,
)
from .reminders import StreamReminderToggle
from .yt_notify import (
    YTChannelSelector,
    YTRoleSelector,
    YTMentionEveryoneToggle,
)

from zenox.enums import Game
from zenox.constants import CODES_CONFIG_NOT_SUPPORTED, REMINDERS_CONFIG_NOT_SUPPORTED, YOUTUBE_NOTIFICATIONS_CONFIG_NOT_SUPPORTED

if TYPE_CHECKING:
    from ....types import Interaction
    from ..view import GuildSettingsUI  # noqa: F401


class ModuleSelector(Select["GuildSettingsUI"]):
    # Replace the Buttons with a selector, where each SelectOption is a module
    def __init__(self, game: Game):
        options = self._get_options(game)
        super().__init__(
            options=options,
            placeholder=LocaleStr(key="guilds.select_module"),
            min_values=1,
            max_values=1,
        )

    def _get_options(self, game: Game) -> list[SelectOption]:
        options = []
        
        if game not in CODES_CONFIG_NOT_SUPPORTED:
            options.append(SelectOption(
            label=LocaleStr(key="guilds.codes_module_label"),
            description=LocaleStr(key="guilds.codes_module_description"),
            value="codes",
            ))
        
        if game not in REMINDERS_CONFIG_NOT_SUPPORTED:
            options.append(SelectOption(
            label=LocaleStr(key="guilds.reminders_module_label"),
            description=LocaleStr(key="guilds.reminders_module_description"),
            value="reminders",
            ))
        
        if game not in YOUTUBE_NOTIFICATIONS_CONFIG_NOT_SUPPORTED:
            options.append(SelectOption(
            label=LocaleStr(key="guilds.yt_notify_module_label"),
            description=LocaleStr(key="guilds.yt_notify_module_description"),
            value="yt_notify",
            ))
        
        return options

    async def callback(self, i: Interaction):
        assert self.view.game is not None

        go_back_button = GoBackButton(
            self.view.children,
            self.view.get_embeds(i.message),
            path_to_bytesio(self.view.filepath),
        )
        self.view.clear_items()

        if self.values[0] == "codes":
            self.view.add_item(ChannelSelector(channel=self.view.guild.codes[self.view.game].channel))
            self.view.add_item(RoleSelector(role=self.view.guild.codes[self.view.game].mention_role))
            self.view.add_item(
                MentionEveryoneToggle(
                    current_toggle=self.view.guild.codes[
                        self.view.game
                    ].mention_everyone
                )
            )
            self.view.add_item(CodesHelpButton())
            self.view.add_item(go_back_button)

        elif self.values[0] == "reminders":
            self.view.add_item(
                StreamReminderToggle(
                    current_toggle=self.view.guild.reminders[
                        self.view.game
                    ].stream_reminder
                )
            )
            self.view.add_item(go_back_button)
        
        elif self.values[0] == "yt_notify":
            self.view.add_item(YTChannelSelector(channel=self.view.guild.youtube_notifications[self.view.game].channel))
            self.view.add_item(YTRoleSelector(role=self.view.guild.youtube_notifications[self.view.game].mention_role))
            self.view.add_item(
                YTMentionEveryoneToggle(
                    current_toggle=self.view.guild.youtube_notifications[
                        self.view.game
                    ].mention_everyone
                )
            )
            self.view.add_item(go_back_button)

        await self.view.update_ui(i)

        # modal = SetupModal(title=LocaleStr(key="guilds.setup_modal_title"))
        # modal.translate(self.view.locale)
        # await i.response.send_modal(modal)
        # await i.response.send_message("Module selected: " + self.values[0], ephemeral=True)
        # Check Config if already Setup if not, edit message with default to none again and start setup view
