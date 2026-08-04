from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.utils import MISSING

from zenox import emojis
from zenox.l10n import LocaleStr, translator
from zenox.utils import split_list_to_chunks

if TYPE_CHECKING:
    from zenox.types import Interaction

    from .view import LayoutView, View

__all__ = ("ChannelSelect", "RoleSelect", "BooleanSelect", "PaginatorSelect", "Select", "SelectOption",)

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

class Select[V_co: View | LayoutView](discord.ui.Select):
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
            options = [SelectOption(label="No options available", value="no_options")]
            disabled = True
        
        super().__init__(
            custom_id=custom_id,
            min_values=min_values,
            max_values=max_values,
            options=options, # pyright: ignore[reportArgumentType]
            disabled=disabled,
            row=row,
            required=required,
        )

        self.locale_str_placeholder = placeholder

        self.original_options: list[SelectOption] | None = None
        self.original_disabled: bool | None = None
        self.original_placeholder: str | None = None
        self.original_min_values: int | None = None
        self.original_max_values: int | None = None

        self.view: V_co
    
    @property
    def options(self) -> list[SelectOption]:
        return self._underlying.options # pyright: ignore[reportReturnType]
    
    @options.setter
    def options(self, value: list[SelectOption]) -> None:
        if not value:
            value = [SelectOption(label="No options available", value="no_options")]
            self.disabled = True
        self._underlying.options = value # pyright: ignore[reportAttributeAccessIssue]
    
    def translate(self, locale: discord.Locale) -> None:
        if self.locale_str_placeholder:
            self.placeholder = translator.translate(self.locale_str_placeholder, locale)[:100]
        
        for option in self.options:

            option.label = translator.translate(option.locale_str_label, locale)[:100]
            option.value = option.value[:100]

            if option.locale_str_description:
                option.description = translator.translate(option.locale_str_description, locale)[:100]
    
    async def set_loading_state(self, interaction: Interaction) -> None:
        """Sets the select to a loading state"""
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
    
    async def unset_loading_state(self, interaction: Interaction) -> None:
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
        self.disabled = self.original_disabled
        self.placeholder = self.original_placeholder
        self.min_values = self.original_min_values
        self.max_values = self.original_max_values

        await self.view._absolute_edit(interaction, view=self.view)
    
    def update_option_defaults(self, *, values: list[str] | None = None) -> None:
        """Updates the default state of options based on the provided values or the current selected values."""
        values = values or self.values

        for option in self.options:
            option.default = option.value in values
    
    def reset_option_defaults(self) -> None:
        """Resets the default state of all options to False."""
        for option in self.options:
            option.default = False
    
class BooleanSelect[ParentViewT](Select):
    # Allow Custom Select Options to be passed in for more flexibility
    def __init__(self, options: list[SelectOption] | None = None, **kwargs) -> None:
        if options is None:
            options = [
                SelectOption(label=LocaleStr(key="choice_yes"), value="1"),
                SelectOption(label=LocaleStr(key="choice_no"), value="0"),
            ]
        super().__init__(options=options, **kwargs)
        
        self.view: ParentViewT

class ChannelSelect[ParentViewT](discord.ui.ChannelSelect):
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

        self.original_disabled: bool | None = None
        self.original_placeholder: str | None = None
        self.original_min_values: int | None = None
        self.original_max_values: int | None = None
        self.original_channel_types: list[discord.ChannelType] | None = None

        self.view: ParentViewT

    def translate(self, locale: discord.Locale) -> None:
        if self.locale_str_placeholder:
            self.placeholder = translator.translate(self.locale_str_placeholder, locale)[:150]

class RoleSelect[ParentViewT](discord.ui.RoleSelect):
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

        self.original_disabled: bool | None = None
        self.original_placeholder: str | None = None
        self.original_min_values: int | None = None
        self.original_max_values: int | None = None

        self.view: ParentViewT

    def translate(self, locale: discord.Locale) -> None:
        if self.locale_str_placeholder:
            self.placeholder = translator.translate(self.locale_str_placeholder, locale)[:150]

PREV_PAGE = SelectOption(
    label=LocaleStr(key="prev_page_option_label"), value="prev_page", emoji="◀️"
)
NEXT_PAGE = SelectOption(
    label=LocaleStr(key="next_page_option_label"), value="next_page", emoji="▶️"
)

class PaginatorSelect[V_co: View | LayoutView](Select):
    def __init__(
        self,
        options: list[SelectOption],
        **kwargs,
    ) -> None:
        if not options:
            options = [SelectOption(label="No options available", value="no_options")]
            kwargs["disabled"] = True
        
        self.page_idx = 0
        self.options_before_split = options
        self._max_values = kwargs.get("max_values", 1)

        self.view: V_co

        super().__init__(options=self.initialize_options(), **kwargs)
    
    def __repr__(self):
        return f"<{self.__class__.__name__} page_idx={self.page_idx} custom_id={self.custom_id}>"
    
    @staticmethod
    def remove_duplicate_options(options: list[SelectOption], existing_options: list[SelectOption]) -> list[SelectOption]:
        """Removes duplicate options from the provided list of options based on their values."""
        values = {option.value for option in existing_options}
        return [option for option in options if option.value not in values]

    def initialize_options(self) -> list[SelectOption]:
        """Initializes the options for the current page, including navigation options if necessary."""
        split_options = split_list_to_chunks(self.options_before_split, 23- self._max_values)

        if not split_options:
            return []
        
        try:
            values = self.values
        except AttributeError:
            values = []
        
        current_options = [
            option
            for option in self.options_before_split
            if option.value in values and option.value not in {NEXT_PAGE.value, PREV_PAGE.value}
        ]

        try:
            split_options[self.page_idx]
        except IndexError:
            self.page_idx = 0
        
        if self.page_idx == 0:
            if len(split_options) > 1:
                return split_options[0]
            current_page_options = self.remove_duplicate_options(current_options, split_options[0])
            return [NEXT_PAGE] + current_page_options + split_options[0]
    
        if self.page_idx == len(split_options) - 1:
            current_page_options = self.remove_duplicate_options(current_options, split_options[-1])
            return [PREV_PAGE] + current_page_options + split_options[-1]
        
        # For all other pages, include both navigation options
        current_page_options = self.remove_duplicate_options(current_options, split_options[self.page_idx])
        return [PREV_PAGE] + [NEXT_PAGE] + current_page_options + split_options[self.page_idx]

    def set_page_based_on_value(self, value: str) -> None:
        """Sets the current page index based on the provided value."""
        options = split_list_to_chunks(self.options_before_split, 23 - self._max_values)

        for idx, page_options in enumerate(options):
            if value in [option.value for option in page_options]:
                self.page_idx = idx
                break
    
    def update_page(self) -> bool:
        updated = False
        if "next_page" in self.values:
            updated = True
            self.page_idx += 1
            self.options = self.initialize_options()
        elif "prev_page" in self.values:
            updated = True
            self.page_idx -= 1
            self.options = self.initialize_options()
        
        if updated:
            for option in self.options:
                option.default = False
            self.update_option_defaults()

            for option in self.options:
                if option.value in {NEXT_PAGE.value, PREV_PAGE.value}:
                    option.default = False
            
            self.max_values = min(self._max_values, len(self.options))
        
        self.translate(self.view.locale)
        return updated
    

        



"""

"""