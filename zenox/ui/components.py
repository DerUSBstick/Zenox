# Modified Version of https://github.com/seriaati/hoyo-buddy/blob/9c3eebc9bc0c6296bc77285a3b015c10b20dbce0/hoyo_buddy/ui/components.py
import discord
import io
import contextlib
from discord.utils import MISSING
from zenox.bot.error_handler import get_error_embed
from ..static.embeds import ErrorEmbed
from ..static.exceptions import InvalidInputError

from typing import Any, Self, Generic, TypeVar, Sequence

from discord.ui.item import Item
from ..static import emojis
from ..l10n import LocaleStr, translator

V = TypeVar("V", bound="View", covariant=True)

class RoleSelect(discord.ui.RoleSelect, Generic[V]):
    def __init__(
            self,
            *,
            custom_id: str = MISSING,
            placeholder: LocaleStr | str | None = None,
            min_values: int = 1,
            max_values: int = 1,
            disabled: bool = False,
            row: int | None = None,
            default_values: list[discord.SelectDefaultValue] = MISSING
    ) -> None:
        super().__init__(
            custom_id=custom_id,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
            default_values=default_values
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
            )[:100]

class ChannelSelect(discord.ui.ChannelSelect, Generic[V]):
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
        default_values: list[discord.SelectDefaultValue] = MISSING
    ) -> None:
        super().__init__(
            channel_types=channel_type,
            custom_id=custom_id,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
            default_values=default_values
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
            )[:100]

class SelectOption(discord.SelectOption):
    def __init__(
        self,
        *,
        label: LocaleStr, 
        value: str,
        description: LocaleStr | str | None = None,
        emoji: str | discord.Emoji | discord.PartialEmoji | None = None,
        default: bool = False
    ) -> None:
        super().__init__(
            label=label if isinstance(label, str) else label.key,
            value=value,
            description=description,
            emoji=emoji,
            default=default
        )
        self.locale_str_label = label
        self.locale_str_description = description

class Select(discord.ui.Select, Generic[V]):
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
    ) -> None:
        super().__init__(
            custom_id=custom_id,
            min_values=min_values,
            max_values=max_values,
            options=options,
            disabled=disabled,
            row=row,
        )
        self.locale_str_placeholder = placeholder

        self.original_placeholder: str | None = None
        self.original_options: list[SelectOption] | None = None
        self.original_disabled: bool | None = None
        self.original_max_values: int | None = None
        self.original_min_values: int | None = None

        self.view: V
    
    @property
    def options(self) -> list[SelectOption]:
        return self._underlying.options
    
    @options.setter
    def options(self, value: list[SelectOption]) -> None:
        self._underlying.options = value
    
    def translate(self, locale: discord.Locale) -> None:
        if self.locale_str_placeholder:
            self.placeholder = translator.translate(
                self.locale_str_placeholder, locale
            )[:100]
        for option in self.options:
            if not isinstance(option, SelectOption):
                continue

            option.label = translator.translate(
                option.locale_str_label, locale
            )[:100]
            option.value = option.value[:100]

            if option.locale_str_description:
                option.description = translator.translate(
                    option.locale_str_description, locale
                )[:100]

    def update_options_defaults(self, *, values: list[str] | None = None) -> None:
        values = values or self.values
        for option in self.options:
            option.default = option.value in values

class Button(discord.ui.Button, Generic[V]):
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
            style=style, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji, row=row
        )

        self.locale_str_label = label
        self.original_label: str | None = None
        self.original_emoji: str | None = None
        self.original_disabled: bool | None = None

        self.view: V

    def translate(self, locale: discord.Locale) -> None:
        if self.locale_str_label:
            self.label = translator.translate(
                self.locale_str_label, locale
            )


# UPDATE: Support for Thumbnail and Embed Image
class GoBackButton(Button, Generic[V]):
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
            if isinstance(item, Button | Select | RoleSelect | ChannelSelect):
                self.view.add_item(item, translate=False)

        kwargs: dict[str, Any] = {"view": self.view}
        if self.embeds is not None:
            kwargs["embeds"] = self.embeds

        if self.byte_obj is not None:
            self.byte_obj.seek(0)

            original_image = None
            for embed in self.embeds or []:
                original_image = (
                    (embed.image.url).split("/")[-1].split("?")[0]
                    if embed.image.url is not None
                    else None
                )
                if original_image is not None:
                    embed.set_image(url=f"attachment://{original_image}")

            original_image = original_image or "image.png"
            kwargs["attachments"] = [discord.File(self.byte_obj, filename=original_image)]

        await interaction.response.edit_message(**kwargs)

class ToggleButton(Button, Generic[V]):
    def __init__(self, current_toggle: bool, toggle_label: LocaleStr, *, disabled: bool = False, custom_id: str | None = None, **kwargs: Any) -> None:
        self.current_toggle = current_toggle
        self.toggle_label = toggle_label
        kwargs["row"] = kwargs.get("row", 1)
        super().__init__(
            style=self._get_style(),
            label=LocaleStr(
                custom_str="{toggle_label}: {status}",
                toggle_label=toggle_label,
                status=self.__get_status(),
            ),
            emoji=emojis.TOGGLE_EMOJIS[current_toggle],
            disabled=disabled,
            custom_id=custom_id,
            **kwargs,
        )

        self.view: V
    
    def _get_style(self) -> discord.ButtonStyle:
        return discord.ButtonStyle.green if self.current_toggle else discord.ButtonStyle.gray

    def __get_status(self) -> LocaleStr:
        return (
            LocaleStr(key="on_button_label") if self.current_toggle 
            else LocaleStr(key="off_button_label")
        )
    
    def update_style(self) -> None:
        self.style = self._get_style()
        self.label = self.toggle_label.translate(self.view.locale) + ": " + self.__get_status().translate(self.view.locale)
        self.emoji = emojis.TOGGLE_EMOJIS[self.current_toggle]
    
    def translate(self, locale: discord.Locale) -> None:
        self.label = translator.translate(self.toggle_label, locale) + ": " + translator.translate(self.__get_status(), locale)

    async def callback(self, interaction: discord.Interaction, *, edit: bool = True, **kwargs: Any) -> Any:
        self.current_toggle = not self.current_toggle
        self.update_style()
        if edit:
            await interaction.response.edit_message(view=self.view, **kwargs)

class URLButtonView(discord.ui.View):
    def __init__(
        self,
        locale: discord.Locale,
        *,
        url: str,
        label: str | LocaleStr | None = None,
        emoji: str | None = None,
    ) -> None:
        super().__init__()
        self.add_item(
            discord.ui.Button(
                label=translator.translate(label, locale) if label else None, url=url, emoji=emoji
            )
        )

class View(discord.ui.View):
    def __init__(
        self,
        *,
        author: discord.User | discord.Member | None,
        locale: discord.Locale,
        timeout: float | None = 180
    ):
        super().__init__(timeout=timeout)
        self.author = author
        self.locale = locale
        self.message: discord.Message | None = None

        self._item_states: dict[str, bool] = {} # Original states of the items to restore after enabling
    
    async def on_timeout(self) -> None:
        if self.message:
            self.disable_items()
            with contextlib.suppress(discord.NotFound, discord.HTTPException):
                await self.message.edit(view=self)
    
    async def on_error(self, interaction: discord.Interaction, error: Exception, item: Item[Any]) -> None:
        locale = interaction.locale
        embed, known = get_error_embed(error, locale)
        if not known:
            interaction.client.capture_exception(error)
        await self.absolute_send(interaction, embed=embed, ephemeral=True)#

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.author is None:
            return True
        
        if self.author.id != interaction.user.id:
            embed = ErrorEmbed(
                interaction.locale,
                title=LocaleStr(key="interaction_failed_title"),
                description=LocaleStr(key="interaction_failed_description")
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True
    
    def update_items(self, custom_ids: list[str], *, disabled: bool = None) -> None:
        for item in self.children:
            if isinstance(item, Button | Select | ChannelSelect | RoleSelect) and item.custom_id in custom_ids:
                if disabled is not None:
                    item.disabled = disabled

    def disable_items(self) -> None:
        for child in self.children:
            if isinstance(child, discord.ui.Button | discord.ui.Select | discord.ui.ChannelSelect | discord.ui.RoleSelect):
                if child.custom_id is not None:
                    self._item_states[child.custom_id] = child.disabled # Store original states for later
                if isinstance(child, discord.ui.Button) and child.url: # Skip all URL Buttons
                    continue
                child.disabled = True

    def enable_items(self) -> None:
        for child in self.children:
            if isinstance(child, discord.ui.Button | discord.ui.Select | discord.ui.ChannelSelect | discord.ui.RoleSelect):
                if isinstance(child, discord.ui.Button) and child.url:
                    continue

                if child.custom_id is not None:
                    child.disabled = self._item_states.get(child.custom_id, False)
                else:
                    # Cannot determine the original state of the item
                    child.disabled = False

    def add_item(self, item: Button | Select | ChannelSelect | RoleSelect, *, translate: bool = True) -> Self:
        if translate:
            item.translate(self.locale)
        return super().add_item(item)

    def get_item(self, custom_id: str) -> Button | Select | ChannelSelect | RoleSelect:
        for item in self.children:
            if isinstance(item, Button | Select | ChannelSelect | RoleSelect) and item.custom_id == custom_id:
                return item

        msg = f"No item found with custom_id {custom_id}"
        raise ValueError(msg)

    def translate_items(self) -> None:
        for item in self.children:
            if isinstance(item, Button | Select | ChannelSelect | RoleSelect):
                item.translate(self.locale)

    @staticmethod
    async def absolute_send(interaction: discord.Interaction, **kwargs: Any) -> None:
        with contextlib.suppress(discord.NotFound):
            if not interaction.response.is_done():
                await interaction.response.send_message(**kwargs)
            else:
                await interaction.followup.send(**kwargs)
    
    @staticmethod
    async def absolute_edit(interaction: discord.Interaction, **kwargs: Any) -> None:
        with contextlib.suppress(discord.NotFound):
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
        label: LocaleStr | str,
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
        is_bool: bool = False,
    ) -> None:
        super().__init__(
            label=label if isinstance(label, str) else "#NoLabel",
            style=style,
            custom_id=custom_id,
            required=required,
            min_length=min_length,
            max_length=max_length,
            row=row,
        )
        self.locale_str_label = label
        self.locale_str_placeholder = placeholder
        self.locale_str_default = default

        self.is_digit = is_digit
        self.max_value = max_value
        self.min_value = min_value
        self.is_bool = is_bool

class Modal(discord.ui.Modal):
    def __init__(
            self,
            *,
            title: LocaleStr | str,
            timeout: float | None = None,
            custom_id: str = MISSING
    ) -> None:
        super().__init__(
            title=title if isinstance(title, str) else "#NoTitle",
            timeout=timeout,
            custom_id=self.__class__.__name__ if custom_id is MISSING else custom_id,
        )
        self.locale_str_title = title
    
    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        locale = interaction.locale
        embed, recognized = get_error_embed(error, locale)
        if not recognized:
            interaction.client.capture_exception(error)

        if not interaction.response.is_done():
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def on_submit(self, interaction: discord.Interaction) -> None:
        self.validate_inputs()
        with contextlib.suppress(discord.NotFound):
            await interaction.response.defer()
        self.stop()

    def translate(self, locale: discord.Locale) -> None:
        self.title = translator.translate(self.locale_str_title, locale)
        for item in self.children:
            if isinstance(item, TextInput):
                item.label = translator.translate(item.locale_str_label, locale)

                if item.is_digit:
                    item.placeholder = f"({item.min_value} ~ {item.max_value})"
                elif item.is_bool:
                    item.placeholder = "0/1"

                if item.locale_str_placeholder:
                    item.placeholder = translator.translate(item.locale_str_placeholder, locale)
                if item.locale_str_default:
                    item.default = translator.translate(item.locale_str_default, locale)
    
    def validate_inputs(self) -> None:
        """Validates all TextInput children of the modal. Raises InvalidInputError if any input is invalid."""
        for item in self.children:
            if isinstance(item, TextInput) and item.is_digit:
                try:
                    value = int(item.value)
                except ValueError as e:
                    raise InvalidInputError(
                        LocaleStr(key="invalid_input.input_needs_to_be_int", input=item.label)
                    ) from e
                if item.max_value is not None and value > item.max_value:
                    raise InvalidInputError(
                        LocaleStr(
                            key="invalid_input.input_out_of_range.max_value", input=item.label, max_value=item.max_value
                        )
                    )
                if item.min_value is not None and value < item.min_value:
                    raise InvalidInputError(
                        LocaleStr(
                            key="invalid_input.input_out_of_range.min_value", min_value=item.min_value, input=item.label
                        )
                    )
            elif isinstance(item, TextInput) and item.is_bool:
                if item.value not in {"0", "1"}:
                    raise InvalidInputError(LocaleStr(key="invalid_input.input_needs_to_be_bool", input=item.label))
    
    @property
    def incomplete(self) -> bool:
        """Returns True if any required TextInput is empty. False otherwise."""
        return any(item.required and not item.value for item in self.children if isinstance(item, TextInput))