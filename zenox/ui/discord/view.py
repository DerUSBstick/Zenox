from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any, Self

import discord

from zenox import emojis
from zenox.bot.error_handler import get_error_embed
from zenox.embeds import ErrorEmbed
from zenox.db.classes import UserConfig
from zenox.l10n import LocaleStr

from .action_row import ActionRow
from .button import Button
from .container import Container
from .section import Section
from .select import ChannelSelect, Select, RoleSelect
from .text_display import TextDisplay

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from zenox.types import Interaction, User

__all__ = ("LayoutView", "View")

type LayoutViewItem = (
    ActionRow
    | Section
    | TextDisplay
    | Container
    | discord.ui.MediaGallery
    | discord.ui.File
    | discord.ui.Separator
)

class ViewMixin:
    children: list[discord.ui.Item[Any]]
    author: User
    user: UserConfig | None
    message: discord.Message | None
    locale: discord.Locale
    clear_items: Callable[[], None]
    item_states: dict[str, bool]

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} author={self.author!r} message={self.message!r} locale={self.locale!r}>"
    
    @staticmethod
    async def _absolute_send(interaction: Interaction, **kwargs: Any) -> None:
        """Sends a message to the interaction, handling whether it has already been responded to."""
        with contextlib.suppress(discord.HTTPException):
            if not interaction.response.is_done():
                await interaction.response.send_message(**kwargs)
            else:
                await interaction.followup.send(**kwargs)
    
    @staticmethod
    async def _absolute_edit(interaction: Interaction, **kwargs: Any) -> None:
        """Edits a message in the interaction, handling whether it has already been responded to."""
        with contextlib.suppress(discord.HTTPException):
            if not interaction.response.is_done():
                await interaction.response.edit_message(**kwargs)
            else:
                await interaction.edit_original_response(**kwargs)
    
    @staticmethod
    def _get_embeds(message: discord.Message | None) -> list[discord.Embed] | None:
        """Retrieves the embeds from a message, if it exists."""
        if message is not None:
            return message.embeds
        return None

    async def on_error(self, interaction: Interaction, error: Exception, item: discord.ui.Item[Any]) -> None:
        """Handles errors that occur during interaction with the view."""
        locale = self.locale
        embed, recognized = get_error_embed(error, locale)
        if not recognized:
            interaction.client.capture_exception(error)

        with contextlib.suppress(Exception):
            await item.unset_loading_state(interaction) # pyright: ignore[reportAttributeAccessIssue]
            await self._absolute_edit(interaction)
        await self._absolute_send(interaction, embed=embed, ephemeral=True)
    
    async def _interaction_check(self, interaction: Interaction) -> bool:
        """Checks if the interaction is valid for this view."""
        if self.author is None:
            return True

        locale = self.locale

        if interaction.user.id != self.author.id:
            embed = ErrorEmbed(
                locale,
                title=LocaleStr(key="interaction_failed.title"),
                description=LocaleStr(key="interaction_failed.description"),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True
    
    def get_item(self, custom_id: str) -> discord.ui.Item[Any] | None:
        """Retrieves an item from the view by its custom_id."""
        for item in self.children:
            if isinstance(item, (Button, Select, ChannelSelect, RoleSelect)) and item.custom_id is not None:
                if item.custom_id == custom_id:
                    return item
        return None
    
    def disable_items(self) -> None:
        for child in self.children:
            if isinstance(child, discord.ui.Button | discord.ui.Select):
                if child.custom_id is not None:
                    self.item_states[child.custom_id] = child.disabled

                if isinstance(child, discord.ui.Button) and child.url:
                    continue

                child.disabled = True

    def enable_items(self) -> None:
        for child in self.children:
            if isinstance(child, discord.ui.Button | discord.ui.Select):
                if isinstance(child, discord.ui.Button) and child.url:
                    continue

                if child.custom_id is not None:
                    child.disabled = self.item_states.get(child.custom_id, False)
                else:
                    # Cannot determine the state of items without a custom_id, so we enable them by default
                    child.disabled = False

class View(discord.ui.View, ViewMixin):
    """A custom view class that extends discord.ui.View and includes additional functionality."""
    def __init__(self, *, author: User, locale: discord.Locale) -> None:
        super().__init__(timeout=600)
        self.author = author
        self.locale = locale
        self.message: discord.Message | None = None
        self.item_states: dict[str, bool] = {}
    
    def add_items(self, items: Iterable[Button | Select | ChannelSelect | RoleSelect]) -> Self:
        for item in items:
            self.add_item(item)
        return self

    def add_item(self, item: Button | Select | ChannelSelect | RoleSelect, *, translate: bool = True) -> Self:
        if translate:
            item.translate(self.locale)
        return super().add_item(item)

    def translate_items(self) -> None:
        for item in self.children:
            if isinstance(item, Button | Select | ChannelSelect | RoleSelect):
                item.translate(self.locale)

    async def on_error(self, i: Interaction, error: Exception, item: discord.ui.Item[Any]) -> None:
        return await ViewMixin.on_error(self, i, error, item)
    
    async def on_timeout(self) -> None:
        only_url_buttons = all(
            item.url for item in self.children if isinstance(item, (discord.ui.Button))
        )
        if self.message is not None and not only_url_buttons:
            self.clear_items()
            with contextlib.suppress(discord.HTTPException):
                await self.message.edit(view=self)

        if self.message is None and not only_url_buttons:
            print(f"View {self!r} timed out without a set message")

    async def interaction_check(self, i: Interaction) -> bool:
        return await ViewMixin._interaction_check(self, i)

class LayoutView(discord.ui.LayoutView, ViewMixin):
    def __init__(self, *, author: User, locale: discord.Locale) -> None:
        super().__init__(timeout=600)
        self.author = author
        self.locale = locale
        self.message: discord.Message | None = None
        self.item_states: dict[str, bool] = {}
        self.children: list[LayoutViewItem]

        self.translate(locale)

    def translate(self, locale: discord.Locale) -> None:
        for child in self.children:
            if isinstance(child, (ActionRow, Container, Section, TextDisplay)):
                child.translate(locale)

    def add_item(self, item: LayoutViewItem, *, translate: bool = True) -> Self:
        if translate and isinstance(item, (ActionRow, Container, Section, TextDisplay)):
            item.translate(self.locale)
        return super().add_item(item)

    def disable_items(self) -> Self:
        for child in self.children:
            if isinstance(child, (Container, Section, ActionRow)):
                child.disable_items()
        return self

    async def on_error(self, i: Interaction, error: Exception, item: discord.ui.Item[Any]) -> None:
        return await ViewMixin.on_error(self, i, error, item)

    async def on_timeout(self) -> None:
        self.disable_items()

        if self.message is not None:
            with contextlib.suppress(ValueError):
                self.add_item(
                    TextDisplay(
                        content=LocaleStr(
                            custom_str="-# {emoji} {text}",
                            emoji=emojis.INFO,
                            text=LocaleStr(key="layout_view_edited"),
                        )
                    )
                )
            with contextlib.suppress(discord.HTTPException):
                await self.message.edit(view=self)

        if self.message is None:
            print(f"View {self!r} timed out without a set message")

    async def interaction_check(self, i: Interaction) -> bool:
        return await ViewMixin._interaction_check(self, i)