from __future__ import annotations

import discord
from typing import TYPE_CHECKING, Any

from ...components import Button, Modal, TextInput, Label

if TYPE_CHECKING:  #
    from ..view import HoyolabCodesUI  # noqa: F401
    from ....types import Interaction

class UpdateImageModal(Modal):
    image: Label[TextInput] = Label(
        text="Enter the new image URL",
        component=TextInput(
            placeholder="https://example.com/image.png",
            required=True
        )
    )

    def __init__(self) -> None:
        super().__init__(title="Update Stream Image")


class UpdateImage(Button["HoyolabCodesUI"]):
    def __init__(self):
        super().__init__(
            label="Update Image",
            style=discord.ButtonStyle.primary
        )
    
    async def callback(self, i: Interaction) -> Any:
        img_modal = UpdateImageModal()
        img_modal.translate(self.view.locale)
        await i.response.send_modal(img_modal)

        await img_modal.wait()
        incomplete = img_modal.incomplete
        if incomplete:
            return

        await self.view.data._update_val("stream_late_image", img_modal.image.component.value)
        await self.view.update_message(i, embed_only=True)

class PublishDevGuild(Button["HoyolabCodesUI"]):
    def __init__(self):
        super().__init__(
            label="Publish to Dev Guild",
            style=discord.ButtonStyle.success
        )
    
    async def callback(self, i: Interaction) -> Any:
        self.view.action = "Dev"
        self.view.guild_id = i.client.config.discord_dev_guild_id

        await self.view._confirm_button(i)

class GuildIdModal(Modal):
    guild_id: Label[TextInput] = Label(
        text="Enter the Guild ID to publish to",
        component=TextInput(
            placeholder="123456789012345678",
            required=True
        )
    )

    def __init__(self) -> None:
        super().__init__(title="Publish to Guild")

class PublishGuild(Button["HoyolabCodesUI"]):
    def __init__(self):
        super().__init__(
            label="Publish to Guild",
            style=discord.ButtonStyle.success
        )
    
    async def callback(self, i: Interaction) -> Any:
        guild_modal = GuildIdModal()
        guild_modal.translate(self.view.locale)
        await i.response.send_modal(guild_modal)

        await guild_modal.wait()
        incomplete = guild_modal.incomplete
        if incomplete:
            return

        try:
            guild_id = int(guild_modal.guild_id.component.value)
        except ValueError:
            return

        self.view.action = "Guild"
        self.view.guild_id = guild_id

        await self.view._confirm_button(i)
    
class PublishGlobal(Button["HoyolabCodesUI"]):
    def __init__(self, disabled: bool):
        super().__init__(
            label="Publish Globally",
            style=discord.ButtonStyle.danger,
            disabled=disabled
        )
    
    async def callback(self, i: Interaction) -> Any:
        self.view.action = "Global"
        self.view.guild_id = None

        await self.view._confirm_button(i)