import discord
import pathlib
from discord import Locale, Member, User

from .items.primaryOptions import LanguageSelector, GameSelector, SupportApprove, PartnerMenu, SupportButton
from .items.gameOptions import *
from .items.pingPreferences import *
from .items.codePreferences import *
from .items.partnerPrimaryOptions import *
from ..components import View, GoBackButton
from ...static.utils import path_to_bytesio
from ...static.embeds import DefaultEmbed
from ...static.enums import Game
from ...db.structures import GuildConfig, CodesConfig, EventReminderConfig, SpecialProgram
from ...static.constants import _supportCache as _cache

class GuildSettingsUI(View):
    def __init__(
            self,
            *,
            author: User | Member,
            locale: Locale,
            settings: GuildConfig
    ):
        super().__init__(author=author, locale=locale)
        self.settings = settings
        self.filepath: str

        self.game: Game | None = None

        self.add_item(LanguageSelector(self.settings.language))
        self.add_item(GameSelector())
        if str(settings.id) in _cache:
            self.add_item(SupportApprove())
        if "PARTNER_GUILD" in settings.flags:
            self.add_item(PartnerMenu())
        self.add_item(SupportButton())
    
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
        theme = "DARK"
        filename = self.get_brand_image_filename(theme, self.settings.language)
        self.filepath = filename
        return discord.File(filename, filename="brand.png")

    def save_setting(self, dataType: CodesConfig | EventReminderConfig, changed_key: str, value: any) -> None:
        self.settings.updateGameConfigValue(self.game, dataType, changed_key, value)

    def conditioned_ui(self, menu: str) -> None:
        match menu:
            case 'GameOptions':
                items = ["ping_preferences_button", "code_preferences_button"]
                condition = self.settings.codes_config[self.game].channel == None
        
        self.update_items(custom_ids=items, disabled=condition)

    async def rebuild_ui(self, interaction: discord.Interaction, menu: str, *, row: int = 4, game: Game = None):
        go_back_button = GoBackButton(self.children, self.get_embeds(interaction.message), path_to_bytesio(self.filepath), row=row)
        self.clear_items()

        match menu:
            case 'GameOptions':
                self.game = game

                CHANNEL_DISABLED_STATE = self.settings.codes_config[game].channel == None

                self.add_item(ConfigChannelSelect(self.settings.codes_config[game].channel))
                self.add_item(pingPreferences(disabled=CHANNEL_DISABLED_STATE, custom_id="ping_preferences_button"))
                self.add_item(codePreferences(disabled=CHANNEL_DISABLED_STATE, custom_id="code_preferences_button"))
                self.add_item(StreamReminderToggle(self.settings.event_reminders[game].config["streams"]))
                self.add_item(TestButton())
            
            case 'PingPreferences':
                self.add_item(PingRoleSelect(self.settings.codes_config[self.game].role_ping))
                self.add_item(EveryonePingToggle(self.settings.codes_config[self.game].everyone_ping))
            
            case 'CodePreferences':
                self.add_item(StreamRedemptionCodeToggle(self.settings.codes_config[self.game].stream_codes))
                self.add_item(AllRedemptionCodesToggle(self.settings.codes_config[self.game].all_codes))
            
            case 'PartnerOptions':
                self.add_item(SetInviteUrlButton())
                self.add_item(SetGuildDescriptionButton())

        self.add_item(go_back_button)
        await interaction.response.edit_message(view=self)

    async def update_ui(self, interaction: discord.Interaction, *, translate: bool = False) -> None:
        if translate:
            self.translate_items()
        await self.absolute_edit(
            interaction,
            embed=self.get_embed(),
            attachments=[self.get_brand_image_file()],
            view=self,
        )

        if not interaction.response.is_done():
            await interaction.response.defer()