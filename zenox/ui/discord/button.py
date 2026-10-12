from __future__ import annotations

from typing import TYPE_CHECKING, Any, Sequence

import discord
import io

from .select import Select, ChannelSelect, RoleSelect

from zenox import emojis
from zenox.l10n import LocaleStr, translator

if TYPE_CHECKING:
    from zenox.types import Interaction

    from .view import LayoutView, View


__all__ = ("Button", "GoBackButton", "ToggleButton", "EmojiToggleButton")


class Button[V_co: View | LayoutView](discord.ui.Button):
    def __init__(
        self,
        *,
        style: discord.ButtonStyle = discord.ButtonStyle.secondary,
        label: LocaleStr | str | None = None,
        disabled: bool = False,
        custom_id: str | None = None,
        url: str | None = None,
        emoji: str | None = None,
        row: int | None = None,
    ) -> None:
        super().__init__(
            style=style,
            disabled=disabled,
            custom_id=custom_id,
            url=url,
            emoji=emoji,
            row=row,
        )

        self.locale_str_label = label

        self.original_label: str | None = None
        self.original_emoji: str | None = None
        self.original_disabled: bool | None = None

        self.view: V_co
    
    def translate(self, locale: discord.Locale) -> None:
        if self.locale_str_label:
            self.label = translator.translate(self.locale_str_label, locale)[:80]

class GoBackButton[V_co: View](Button):
    def __init__(
        self,
        original_children: list[discord.ui.Item[Any]],
        embeds: Sequence[discord.Embed] | None = None,
        byte_obj: io.BytesIO | None = None,
        row: int = 4,
    ) -> None:
        super().__init__(emoji=emojis.BACK, row=row)
        self.original_children = original_children.copy()
        self.embeds = embeds
        self.byte_obj = byte_obj

        self.view: V_co

    async def callback(self, interaction: Interaction) -> Any:
        self.view.clear_items()
        for item in self.original_children:
            if isinstance(item, Button | Select | ChannelSelect | RoleSelect):
                self.view.add_item(item, translate=False)

        kwargs: dict[str, Any] = {"view": self.view}
        original_image = None
        if self.embeds is not None:
            kwargs["embeds"] = self.embeds

        if self.byte_obj is not None:
            self.byte_obj.seek(0)

            original_image = None
            for embed in self.embeds or []:
                if embed.image.url is not None:
                    original_image = embed.image.url.split("/")[-1].split("?")[0]
                    embed.set_image(url=f"attachment://{original_image}")

            original_image = original_image or "image.png"
            kwargs["attachments"] = [
                discord.File(self.byte_obj, filename=original_image)
            ]

        await interaction.response.edit_message(**kwargs)

class ToggleButton[V_co: View](Button):
    def __init__(
        self,
        current_toggle: bool,
        toggle_label: LocaleStr,
        *,
        disabled: bool = False,
        custom_id: str | None = None,
        row: int | None = None,
    ):
        self.current_toggle = current_toggle
        self.toggle_label = toggle_label
        super().__init__(
            style=self._get_style(),
            label=LocaleStr(
                custom_str="{toggle_label}: {status}",
                toggle_label=self.toggle_label,
                status=self._get_status(),
            ),
            emoji=emojis.TOGGLE[current_toggle],
            disabled=disabled,
            custom_id=custom_id,
            row=row,
        )

        self.view: V_co

    def _get_style(self) -> discord.ButtonStyle:
        """Returns the appropriate button style based on the current toggle state."""
        return (
            discord.ButtonStyle.green
            if self.current_toggle
            else discord.ButtonStyle.gray
        )

    def _get_status(self) -> LocaleStr:
        """Returns the localized status text based on the current toggle state."""
        return (
            LocaleStr(key="on_button_label")
            if self.current_toggle
            else LocaleStr(key="off_button_label")
        )

    def update_style(self) -> None:
        """Updates the button's visual appearance to reflect the current toggle state."""
        self.style = self._get_style()
        self.label = (
            self.toggle_label.translate(self.view.locale)
            + ": "
            + self._get_status().translate(self.view.locale)
        )
        self.emoji = emojis.TOGGLE[self.current_toggle]

    def translate(self, locale: discord.Locale) -> None:
        self.label = translator.translate(
            LocaleStr(
                custom_str="{toggle_label}: {state}",
                toggle_label=self.toggle_label,
                state=self._get_status(),
            ),
            locale,
        )

    async def callback(
        self, interaction: Interaction, *, edit: bool = True, **kwargs: Any
    ) -> Any:
        self.current_toggle = not self.current_toggle
        self.update_style()
        if edit:
            await interaction.response.edit_message(view=self.view, **kwargs)

class EmojiToggleButton[V_co: View | LayoutView](Button):
    def __init__(self, *, current: bool, **kwargs) -> None:
        super().__init__(**kwargs)
        self.current = current
        self.update_style()

        self.view: V_co

    def update_style(self) -> None:
        self.emoji = emojis.TOGGLE[self.current]
        self.style = discord.ButtonStyle.green if self.current else discord.ButtonStyle.gray