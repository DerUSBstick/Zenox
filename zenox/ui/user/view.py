import discord
import pathlib
from discord import Locale, Member, User

from .items.primaryOptions import LanguageSelector, DarkModeToggle                                                                                                                       
from ..components import View
from ...static.embeds import DefaultEmbed
from zenox.db.structures import UserSettings, UserConfig

class UserSettingsUI(View):
    def __init__(
        self,
        *,
        author: User | Member,
        locale: Locale,
        settings: UserSettings
    ):
        super().__init__(author=author, locale=locale)
        self.settings = settings

        self.add_item(LanguageSelector(self.settings.language))
        self.add_item(DarkModeToggle(settings.dark_mode))
    
    @staticmethod
    def get_brand_image_filename(theme: str, locale: discord.Locale) -> str:
        filename = f"zenox-assets/assets/brand/{theme}-{locale.value}.png"
        if not pathlib.Path(filename).exists():
            return f"zenox-assets/assets/brand/{theme}-en-US.png"
        return filename

    def get_embed(self) -> DefaultEmbed:
        embed = DefaultEmbed(self.locale)
        embed.set_image(url="attachment://brand.png")
        return embed
    
    def get_brand_image_file(self) -> discord.File:
        theme = "DARK" if self.settings.dark_mode else "LIGHT"
        filename = self.get_brand_image_filename(theme, self.settings.language)
        return discord.File(filename, filename="brand.png")
    
    async def update_ui_and_save_settings(self, interaction: discord.Interaction, *, translate: bool = False) -> None:
        if translate:
            self.translate_items()
        await self.absolute_edit(
            interaction,
            embed=self.get_embed(),
            attachments=[self.get_brand_image_file()],
            view=self,
        )

        # Update Settings
        config = UserConfig(interaction.user.id).updateSettings(self.settings)