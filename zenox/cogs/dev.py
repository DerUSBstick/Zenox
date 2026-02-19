from __future__ import annotations

import discord
import datetime
import pytz
from discord import app_commands
from discord.app_commands import locale_str
from discord.ext import commands
from typing import TYPE_CHECKING

from zenox import emojis
from zenox.l10n import LocaleStr
from zenox.db.mongodb import DB
from zenox.db.classes import Guild, SpecialProgram
from zenox.embeds import DefaultEmbed
from zenox.enums import Game
from zenox.constants import ZENOX_LOCALES, HOYO_OFFICIAL_CHANNELS
from zenox.ui.components import Modal, TextInput, Label
from zenox.utils import send_webhook

if TYPE_CHECKING:
    from ..bot import Zenox
    from ..types import Interaction

class ConfirmScheduleModal(Modal):
    confirm = Label(text="Enter anything to confirm. Cannot undo.", component=TextInput(placeholder="Type anything to confirm", required=False))

@app_commands.guild_install()
class Dev(commands.GroupCog, group_name="dev"):
    def __init__(self, client: Zenox):
        self.client = client

    # cog_check is for regular commands
    # https://github.com/Rapptz/discord.py/discussions/9161
    @staticmethod
    def is_owner(i: Interaction):
        return i.user.id == 585834029484343298

    @app_commands.command(
            name=locale_str("guild_config"),
            description=locale_str("View RAW Guild Configuration")
    )
    @app_commands.check(is_owner)
    async def guild_config(self, i: Interaction, guild_id: str):
        raw_config = await DB.guilds.find_one({"id": int(guild_id)})
        if not raw_config:
           return await i.response.send_message(f"No Data found for `{guild_id}`", ephemeral=True) 
        embed = DefaultEmbed(locale=discord.Locale.american_english, title=f"Raw Data for `{guild_id}`", description=f"```json\n{raw_config}\n```")
        embed.set_footer(text=f"Description Length: {len(str(raw_config))}")
        return await i.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(
            name=locale_str("schedule_stream"),
            description=locale_str("Schedule a Stream")
    )
    @app_commands.check(is_owner)
    async def schedule_stream(self, i: Interaction, game: Game, version: str, *, title: str, start: int, end: int, image: discord.Attachment):
        if i.client.db_config is None:
            return await i.response.send_message("Bot configuration is not loaded yet. Please try again later.", ephemeral=True)
        
        await i.client.db_config._update_module_setting(module_name="stream_codes_config", game=game, setting="stream_time", value=start)
        await i.client.db_config._update_module_setting(module_name="stream_codes_config", game=game, setting="version", value=version)

        special_program = await SpecialProgram.new(game=game, version=version, stream_start_time=start, stream_end_time=end, stream_title=title, stream_early_image=image)
        if special_program.stream_reminder_published:
            return await i.response.send_message(f"Stream for {game.value} {version} is already scheduled and reminder has been published.", ephemeral=True)
        
        modal = ConfirmScheduleModal(title="Confirm Scheduling Stream")
        await i.response.send_modal(modal)
        state = await modal.wait()
        if state:
            return
        
        _success, _forbidden, _failed = await self._create_events(i.client, special_program)
        await special_program._update_val("stream_reminder_published", True)

        await i.followup.send(f"Scheduled Stream for {game.value} {version}. Successfully created events in {_success} guilds, failed in {_failed} guilds, and missing permissions in {_forbidden} guilds.", ephemeral=True)
        await send_webhook(
            client=i.client,
            webhook_url=i.client.config.webhook_url,
            content=f"Scheduled Stream for {game.value} {version}. Successfully created events in {_success} guilds, failed in {_failed} guilds, and missing permissions in {_forbidden} guilds."
        )
    
    @classmethod
    def _pre_translate_schedule_stream(cls, data: SpecialProgram) -> dict[discord.Locale, dict[str, str]]:
        _translations: dict[discord.Locale, dict[str, str]] = {}
        for locale in ZENOX_LOCALES:
            _translations[locale] = {
                "name": LocaleStr(key="stream_reminders_name", version=data.version, title=data.stream_title).translate(locale),
                "description": LocaleStr(key="stream_reminders_description", youtube=emojis.YOUTUBE, twitch=emojis.TWITCH, youtube_url=HOYO_OFFICIAL_CHANNELS[data.game]["YouTube"], twitch_url=HOYO_OFFICIAL_CHANNELS[data.game]["Twitch"]).translate(locale)
            }
        
        return _translations

    @classmethod
    async def _create_events(cls, client: Zenox, data: SpecialProgram) -> tuple[int, int, int]:
        _success, _forbidden, _failed = 0, 0, 0
        _translations = cls._pre_translate_schedule_stream(data)

        # Find only guilds that have stream reminders enabled for this game
        cursor = DB.guilds.find({f"reminders.{data.game.value}.stream_reminder": True}, {"id": 1, "_id": 0})
        async for guild_data in cursor:
            try:
                guild = await Guild.new(guild_data["id"])

                guild_obj = client.get_guild(guild.id) or await client.fetch_guild(guild.id)

                await guild_obj.create_scheduled_event(
                    name=_translations[guild.language]["name"],
                    description=_translations[guild.language]["description"],
                    start_time=datetime.datetime.fromtimestamp(data.stream_start_time, pytz.UTC),
                    end_time=datetime.datetime.fromtimestamp(data.stream_end_time, pytz.UTC),
                    location=HOYO_OFFICIAL_CHANNELS[data.game]["Twitch"],
                    image=data.stream_early_image,
                    entity_type=discord.EntityType.external,
                    privacy_level=discord.PrivacyLevel.guild_only
                )
                _success += 1
            except discord.Forbidden:
                _forbidden += 1
            except Exception as e:
                client.capture_exception(e)
                _failed += 1

        return _success, _forbidden, _failed

async def setup(client: Zenox) -> None:
    await client.add_cog(Dev(client))
