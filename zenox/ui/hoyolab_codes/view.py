from __future__ import annotations

import discord
from typing import TYPE_CHECKING, Literal

from .items.buttons import UpdateImage, PublishDevGuild, PublishGuild, PublishGlobal
from .items.confirm import ConfirmButton
from ..components import View, GoBackButton
from ...db.classes import SpecialProgram

if TYPE_CHECKING:
    from ...types import Interaction, User

class HoyolabCodesUI(View):
    def __init__(self, *, author: User, locale: discord.Locale, data: SpecialProgram):
        super().__init__(author=author, locale=locale)
        
        self.data = data
        self.action: Literal["Global", "Guild", "Dev"] | None = None
        self.guild_id: int | None = None

        allow_publish = (self.data.codes_count != 0 and self.data.codes_count == len(self.data.codes) and not self.data.codes_published)
        print(self.data.codes_count != 0, self.data.codes_count == len(self.data.codes), not self.data.codes_published)
        self.add_item(UpdateImage())
        self.add_item(PublishDevGuild())
        self.add_item(PublishGuild())
        self.add_item(PublishGlobal(disabled=not allow_publish))

    async def _confirm_button(self, i: Interaction):
        go_back_button = GoBackButton(self.children)
        self.clear_items()

        self.add_item(ConfirmButton())
        self.add_item(go_back_button)

        if not i.response.is_done():
            await i.response.edit_message(view=self)
        else:
            if i.message:
                await i.followup.edit_message(message_id=i.message.id, view=self)

    async def update_message(self, i: Interaction, *, embed_only: bool = False) -> None:
        from zenox.auto_tasks.check_codes import CheckCodes
        assert i.client.db_config is not None
        stream_config = i.client.db_config.stream_codes_config[self.data.game]
        await CheckCodes._update_message(stream_config.channel, stream_config.message, self.data, client=i.client, embed_only=embed_only)

