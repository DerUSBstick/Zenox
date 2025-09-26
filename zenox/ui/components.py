from __future__ import annotations

import discord
import contextlib
import io
from discord.utils import MISSING
from discord.ui.item import Item
from typing import Any, Sequence, Self, TYPE_CHECKING

from .. import emojis
from ..bot.error_handler import get_error_embed
from ..embeds import ErrorEmbed
from ..l10n import LocaleStr, translator
from ..exceptions import InvalidInputError

if TYPE_CHECKING:
    from ..types import Interaction, User


class View(discord.ui.View):
    def __init__(self, *, author: User, locale: discord.Locale) -> None:
        super().__init__(timeout=240)
        self.author = author
        self.locale = locale
        self.message: discord.Message | None = None
        self.item_states: dict[str, bool] = {}

    async def on_timeout(self) -> None:
        if self.message:
            self.disable_items()
            with contextlib.suppress(discord.NotFound, discord.HTTPException):
                await self.message.edit(view=self)

    async def on_error(
        self, interaction: Interaction, error: Exception, item: Item[Any]
    ):
        locale = self.locale
        embed, known = get_error_embed(error, locale)
        if not known:
            interaction.client.capture_exception(error)
        await self.absolute_send(interaction, embed=embed, ephemeral=True)

    async def interaction_check(self, interaction: Interaction) -> bool:
        if self.author is None or self.author.id == interaction.user.id:
            return True

        embed = ErrorEmbed(
            self.locale,
            title=LocaleStr(key="interaction_failed.title"),
            description=LocaleStr(key="interaction_failed.description"),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return False

    def disable_items(self) -> None:
        """Disables all interactive components while preserving their original states."""
        for child in self.children:
            if isinstance(child, (Button, Select, ChannelSelect, RoleSelect)):
                if child.custom_id is not None:
                    self.item_states[child.custom_id] = child.disabled

                if isinstance(child, discord.ui.Button) and child.url:
                    continue

                child.disabled = True

    def enable_items(self) -> None:
        """Restores all interactive components to their previously saved states."""
        for child in self.children:
            if isinstance(child, (Button, Select, ChannelSelect, RoleSelect)):
                if isinstance(child, discord.ui.Button) and child.url:
                    continue

                if child.custom_id is not None:
                    child.disabled = self.item_states.get(child.custom_id, False)
                else:
                    child.disabled = False

    def add_item(
        self,
        item: "Button | Select | ChannelSelect | RoleSelect",
        *,
        translate: bool = True,
    ) -> Self:
        if translate:
            item.translate(self.locale)
        return super().add_item(item)

    def translate_items(self) -> None:
        """Translates all translatable child components to the view's locale."""
        for child in self.children:
            if isinstance(child, Button | Select | ChannelSelect | RoleSelect):
                child.translate(self.locale)

    @staticmethod
    async def absolute_send(interaction: discord.Interaction, **kwargs: Any) -> None:
        """Sends a message via response or followup, handling already-used responses gracefully."""
        with contextlib.suppress(discord.HTTPException):
            if not interaction.response.is_done():
                # Use original response if not yet used
                await interaction.response.send_message(**kwargs)
            else:
                # Create followup message if response was already used
                await interaction.followup.send(**kwargs)

    @staticmethod
    async def absolute_edit(interaction: discord.Interaction, **kwargs: Any) -> None:
        """Edits a message via response or original response, handling already-used responses gracefully."""
        with contextlib.suppress(discord.HTTPException):
            if not interaction.response.is_done():
                await interaction.response.edit_message(**kwargs)
            else:
                await interaction.edit_original_response(**kwargs)

    @staticmethod
    def get_embeds(message: discord.Message | None) -> list[discord.Embed] | None:
        if message:
            return message.embeds
        return None


class TextInput(discord.ui.TextInput):
    def __init__(
        self,
        *,
        style: discord.TextStyle = discord.TextStyle.short,
        custom_id: str = MISSING,
        placeholder: LocaleStr | str | None = None,
        default: LocaleStr | str | None = None,
        required: bool = True,
        min_length: int | None = None,
        max_length: int | None = None,
        row: int | None = None,
        is_digit: bool = False,
        max_value: int | None = None,
        min_value: int | None = None,
    ) -> None:
        super().__init__(
            style=style,
            custom_id=custom_id,
            required=required,
            min_length=min_length,
            max_length=max_length,
            row=row,
        )
        self.locale_str_placeholder = placeholder
        self.locale_str_default = default

        self.is_digit = is_digit
        self.max_value = max_value
        self.min_value = min_value

    def translate(self, locale: discord.Locale) -> None:
        # if it's self.is_digit and not self.placeholder
        if self.is_digit and not self.locale_str_placeholder:
            if self.min_value is not None and self.max_value is not None:
                self.placeholder = f"{self.min_value} - {self.max_value}"
            elif self.min_value is not None:
                self.placeholder = f"≥ {self.min_value}"
            elif self.max_value is not None:
                self.placeholder = f"≤ {self.max_value}"

        if self.locale_str_placeholder:
            self.placeholder = translator.translate(
                self.locale_str_placeholder, locale
            )[:150]
        if self.locale_str_default:
            self.default = translator.translate(self.locale_str_default, locale)[:4000]


class TextDisplay(discord.ui.TextDisplay):
    def __init__(self, *, content: LocaleStr | str) -> None:
        super().__init__(content=content if isinstance(content, str) else "#NoTrans")
        self.locale_str_content = content

    def translate(self, locale: discord.Locale) -> None:
        self.content = translator.translate(self.locale_str_content, locale)[:4000]


class RoleSelect[V: View](discord.ui.RoleSelect):
    def __init__(
        self,
        *,
        custom_id: str = MISSING,
        placeholder: LocaleStr | str | None = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        row: int | None = None,
        default_values: list[discord.SelectDefaultValue] = MISSING,
    ) -> None:
        super().__init__(
            custom_id=custom_id,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
            default_values=default_values,
        )

        self.locale_str_placeholder = placeholder

        self.original_placeholder: str | None = None
        self.original_disabled: bool | None = None
        self.original_max_values: int | None = None
        self.original_min_values: int | None = None

        self.view: V

    def translate(self, locale: discord.Locale) -> None:
        if self.locale_str_placeholder:
            self.placeholder = translator.translate(
                self.locale_str_placeholder, locale
            )[:150]


class ChannelSelect[V: View](discord.ui.ChannelSelect):
    def __init__(
        self,
        *,
        channel_type: list[discord.ChannelType] = MISSING,
        custom_id: str = MISSING,
        placeholder: LocaleStr | str | None = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        row: int | None = None,
        default_values: list[discord.SelectDefaultValue] = MISSING,
    ) -> None:
        super().__init__(
            channel_types=channel_type,
            custom_id=custom_id,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
            default_values=default_values,
        )
        self.locale_str_placeholder = placeholder

        self.original_placeholder: str | None = None
        self.original_channel_type: list[discord.ChannelType] = MISSING
        self.original_disabled: bool | None = None
        self.original_max_values: int | None = None
        self.original_min_values: int | None = None

        self.view: V

    def translate(self, locale: discord.Locale) -> None:
        if self.locale_str_placeholder:
            self.placeholder = translator.translate(
                self.locale_str_placeholder, locale
            )[:150]


class SelectOption(discord.SelectOption):
    def __init__(
        self,
        *,
        label: LocaleStr | str,
        value: str,
        description: LocaleStr | str | None = None,
        emoji: str | None = None,
        default: bool = False,
    ) -> None:
        super().__init__(
            label=label if isinstance(label, str) else label.identifier,
            value=value,
            emoji=emoji,
            default=default,
        )
        self.locale_str_label = label
        self.locale_str_description = description


class Select[V: View](discord.ui.Select):
    def __init__(
        self,
        *,
        custom_id: str = MISSING,
        placeholder: LocaleStr | str | None = None,
        min_values: int = 1,
        max_values: int = 1,
        options: list[SelectOption],
        disabled: bool = False,
        row: int | None = None,
        required: bool = False,
    ) -> None:
        if not options:
            options = [SelectOption(label="No options", value="0")]
            disabled = True
        super().__init__(
            custom_id=custom_id,
            min_values=min_values,
            max_values=max_values,
            options=options,  # pyright: ignore[reportArgumentType]
            disabled=disabled,
            row=row,
            required=required,
        )
        self.locale_str_placeholder = placeholder

        self.original_placeholder: str | None = None
        self.original_options: list[SelectOption] | None = None
        self.original_disabled: bool | None = None
        self.original_min_values: int | None = None
        self.original_max_values: int | None = None

        self.view: V

    @property
    def options(self) -> list[SelectOption]:
        return self._underlying.options  # pyright: ignore[reportReturnType]

    @options.setter
    def options(self, value: list[SelectOption]) -> None:
        if not value:
            value = [SelectOption(label="No options", value="0")]
            self.disabled = True
        self._underlying.options = value  # pyright: ignore[reportAttributeAccessIssue]

    def translate(self, locale: discord.Locale) -> None:
        if self.locale_str_placeholder:
            self.placeholder = translator.translate(
                self.locale_str_placeholder, locale
            )[:100]

        for option in self.options:
            if not isinstance(option, SelectOption):  # pyright: ignore[reportUnnecessaryIsInstance]
                continue

            option.label = translator.translate(option.locale_str_label, locale)[:100]
            option.value = option.value[:100]

            if option.locale_str_description:
                option.description = translator.translate(
                    option.locale_str_description, locale
                )[:100]

    async def set_loading_state(self, interaction: discord.Interaction) -> None:
        """Sets the select to a loading state"""
        # Try Modals to see if self.parent can detect it later
        self.original_options = self.options.copy()
        self.original_disabled = self.disabled
        self.original_placeholder = self.placeholder[:] if self.placeholder else None
        self.original_min_values = self.min_values
        self.original_max_values = self.max_values

        self.view.disable_items()

        self.options = [
            SelectOption(
                label=translator.translate(
                    LocaleStr(key="loading_text"), self.view.locale
                ),
                value="loading",
                default=True,
                emoji=emojis.LOADING,
            )
        ]
        self.disabled = True
        self.min_values = 1
        self.max_values = 1

        await self.view.absolute_edit(interaction, view=self.view)

    async def unset_loading_state(
        self, interaction: discord.Interaction, **kwargs
    ) -> None:
        """Restores the select from loading state to its original configuration."""
        if (
            not self.original_options
            or self.original_disabled is None
            or self.original_min_values is None
            or self.original_max_values is None
        ):
            raise RuntimeError("Unset loading state called before set loading state")

        self.view.enable_items()

        self.options = self.original_options

        # Restore other properties
        self.disabled = self.original_disabled
        self.placeholder = self.original_placeholder
        self.min_values = self.original_min_values
        self.max_values = self.original_max_values

        await self.view.absolute_edit(interaction, view=self.view, **kwargs)


class BooleanSelect[V: View](Select):
    def __init__(self, **kwargs) -> None:
        options = [
            SelectOption(label=LocaleStr(key="choice_yes"), value="1"),
            SelectOption(label=LocaleStr(key="choice_no"), value="0"),
        ]
        super().__init__(options=options, **kwargs)
        self.view: V


class Modal(discord.ui.Modal):
    def __init__(
        self,
        *,
        title: LocaleStr | str,
        timeout: float | None = None,
        custom_id: str = MISSING,
    ) -> None:
        super().__init__(
            title=title if isinstance(title, str) else "#NoTitle",
            timeout=timeout,
            custom_id=self.__class__.__name__ if custom_id is MISSING else custom_id,
        )
        self.locale_str_title = title

    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        locale = interaction.locale
        embed, recognized = get_error_embed(error, locale)
        if not recognized:
            interaction.client.capture_exception(error)

        if not interaction.response.is_done():
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(embed=embed, ephemeral=True)

    async def on_submit(self, interaction: Interaction) -> None:
        self.validate_inputs()
        with contextlib.suppress(discord.NotFound):
            await interaction.response.defer()
        self.stop()

    def translate(self, locale: discord.Locale) -> None:
        """Translates the modal title and all child components to the specified locale."""
        self.title = translator.translate(self.locale_str_title, locale)
        for item in self.children:
            if isinstance(item, (Label, Select, TextInput, TextDisplay)):
                item.translate(locale)

    def validate_inputs(self) -> None:
        """Validates all input components of the modal. Raises InvalidInputError if any input is invalid."""
        for item in self.children:
            component = item.component if isinstance(item, Label) else item

            if isinstance(component, TextInput):
                item_text = item.text if isinstance(item, Label) else component.label

                try:
                    value = int(component.value)
                except ValueError as e:
                    raise InvalidInputError(
                        LocaleStr(
                            key="invalid_input.input_needs_to_be_int", input=item_text
                        )
                    ) from e

                if component.max_value is not None and value > component.max_value:
                    raise InvalidInputError(
                        LocaleStr(
                            key="invalid_input.input_out_of_range.max_value",
                            input=item_text,
                            max_value=component.max_value,
                        )
                    )

                if component.min_value is not None and value < component.min_value:
                    raise InvalidInputError(
                        LocaleStr(
                            key="invalid_input.input_out_of_range.min_value",
                            input=item_text,
                            min_value=component.min_value,
                        )
                    )

    @property
    def incomplete(self) -> bool:
        """Returns True if any required input component is empty/unselected. False otherwise."""
        return any(
            (isinstance(item, TextInput) and item.required and not item.value)
            or (
                isinstance(item, Select)
                and item.required
                and not hasattr(item, "values")
            )
            for item in self.children
        )


class Label[T](discord.ui.Label):
    def __init__(
        self,
        *,
        text: LocaleStr | str,
        component: Select | TextInput | ChannelSelect | RoleSelect,
        description: str | LocaleStr | None = None,
    ) -> None:
        super().__init__(
            text=text if isinstance(text, str) else "#NoTrans",
            component=component,
            description=description
            if isinstance(description, str) or description is None
            else "#NoTrans",
        )
        self.locale_str_text = text
        self.locale_str_description = description
        self.component: T

    def translate(self, locale: discord.Locale) -> None:
        """Translate the label's text and description using the provided locale."""
        self.text = translator.translate(self.locale_str_text, locale)[:45]

        if self.locale_str_description:
            self.description = translator.translate(
                self.locale_str_description, locale
            )[:100]

        if isinstance(self.component, (Select, TextInput, ChannelSelect, RoleSelect)):
            self.component.translate(locale)


class Button[V: View](discord.ui.Button):
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

        self.view: V

    def translate(self, locale: discord.Locale) -> None:
        if self.locale_str_label:
            self.label = translator.translate(self.locale_str_label, locale)[:80]


class GoBackButton[V: View](Button[V]):
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

        self.view: V

    async def callback(self, interaction: discord.Interaction) -> Any:
        self.view.clear_items()
        for item in self.original_children:
            if isinstance(item, (Button, Select, ChannelSelect, RoleSelect)):
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


class ToggleButton[V: View](Button):
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

        self.view: V

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
        self, interaction: discord.Interaction, *, edit: bool = True, **kwargs: Any
    ) -> Any:
        self.current_toggle = not self.current_toggle
        self.update_style()
        if edit:
            await interaction.response.edit_message(view=self.view, **kwargs)
