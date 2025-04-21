import genshin
import discord
import pytz
import os
from typing import Literal, TYPE_CHECKING
from discord import app_commands
from discord.app_commands import locale_str
from discord.ext import commands
import datetime, random, time
from ..bot.bot import Zenox
from ..db.mongodb import DB
from ..db.structures import EventReminder, GuildConfig, EventReminderConfig
from ..static.constants import ZENOX_LOCALES, HOYO_OFFICIAL_CHANNELS, _supportCache as _cache
from ..static.enums import Game
from ..static.embeds import Embed
from ..static.emojis import YOUTUBE, TWITCH
from ..static.utils import send_webhook
from ..ui.dev import confirmModal
from ..l10n import LocaleStr

@app_commands.guild_install()
class Dev(commands.GroupCog, group_name="dev"):
    def __init__(self, client: Zenox):
        self.client = client
    
    # cog_check is for regular commands
    # https://github.com/Rapptz/discord.py/discussions/9161
    def is_owner(i: discord.Interaction):
        return i.user.id == 585834029484343298

    @app_commands.command(
        name=locale_str("shards"),
        description=locale_str("Display Shard Information")
    )
    @app_commands.check(is_owner)
    async def shards(self, interaction: discord.Interaction):
        embed = Embed(
            locale=discord.Locale("en-US"),
            color=0x005fff,
            title="Shard Informations"
        )
        
        for shard in self.client.shards.values():
            shard_id = shard.id
            latency = shard.latency*1000  # Convert to ms
            embed.add_field(
                name=f"Shard [{shard_id}]:",
                value=f"**Latency:** `{latency:.0f}ms`\n",
                inline=True
            )
        await interaction.response.send_message(embed=embed) 

    @app_commands.command(
        name=locale_str("request"),
        description=locale_str("Request Permission Check for Guild")
    )
    @app_commands.check(is_owner)
    async def request(self, interaction: discord.Interaction, guildid: str, locale: Literal["en-US", "de"]):
        if guildid in _cache:
            return await interaction.response.send_message(f"There's a pending approval", ephemeral=True)
        if self.client.db.guilds.find_one({"id": int(guildid)}) is None:
            return await interaction.response.send_message(f"The bot is not in the guild with ID `{guildid}`", ephemeral=True)
        
        num = random.randint(1000, 9999)
        start = round(time.time())

        embed = Embed(
            locale=discord.Locale(locale),
            color=0x005fff,
            title=LocaleStr(key="request_embed.title"),
            description=LocaleStr(key="request_embed.description", code=num, expire=f"<t:{start+86400}:R>")
        )

        await interaction.response.send_message(embed=embed)

        message = await interaction.original_response()

        _cache[guildid] = {
            "number": num,
            "channelID": interaction.channel.id,
            "messageID": message.id,
            "start": start,
            "locale": locale
        }

    @app_commands.command(
            name=locale_str("guild_config"),
            description=locale_str("View RAW Guild Configuration")
    )
    @app_commands.check(is_owner)
    async def view_config(self, interaction: discord.Interaction[Zenox], guild_id: str, ephemeral: bool = True):
        raw_config = DB.guilds.find_one({"id": int(guild_id)})
        if not raw_config:
           return await interaction.response.send_message(f"No Data found for `{guild_id}`", ephemeral=ephemeral) 
        embed = discord.Embed(title=f"Raw Data for `{guild_id}`", description=f"```json\n{raw_config}\n```")
        embed.set_footer(text=f"Description Length: {len(str(raw_config))}")
        return await interaction.response.send_message(embed=embed, ephemeral=ephemeral)

    @app_commands.command(
        name=locale_str("schedule_stream"),
        description=locale_str("Schedule a Stream and update config")
    )
    @app_commands.check(is_owner)
    async def schedule_stream(self, interaction: discord.Interaction[Zenox], game: Game, version: str, title: str, start: int, end: int, image: discord.Attachment):
        conf = interaction.client.config.auto_stream_codes_config[game]
        conf.disabled = False
        conf.stream_time = start
        conf.version = version
        interaction.client.config.update_class_config(game, conf)
        interaction.client.config.update_config_file()

        event_data = EventReminder(game=game, version=version)
        if event_data.published:
            return await interaction.response.send_message(f"Version {version} has been published already", ephemeral=True)
        
        confirm_modal = confirmModal(title="Confirmation Modal", timeout=30)
        await interaction.response.send_modal(confirm_modal)
        state = await confirm_modal.wait()
        if state:
            return
        
        await image.save(f"./zenox-assets/assets/event-reminders/{image.filename}")
        event_data._update_val("title", title)
        event_data._update_val("start", datetime.datetime.fromtimestamp(start, pytz.UTC))
        event_data._update_val("end", datetime.datetime.fromtimestamp(end, pytz.UTC))
        event_data._update_val("image", image.filename)

        _success, _forbidden, _failed = await self._create_events(interaction.client, event_data)

        event_data._update_val("published", True)

        await interaction.followup.send(f"Successfully scheduled {game} stream for {version} in {_success} guilds. {_forbidden} guilds missing create event permissions. {_failed} guilds failed to create event.", ephemeral=True)
        await send_webhook(interaction.client.log_webhook_url, content=f"Successfully scheduled {game} stream for {version} in {_success} guilds. {_forbidden} guilds missing create event permissions. {_failed} guilds failed to create event.")

    @classmethod
    def _pre_translate_schedule_stream(self, eventData: EventReminder) -> dict[discord.Locale, dict[str, str]]:
        _translations: dict[discord.Locale, dict[str, str]] = {}
        for language in ZENOX_LOCALES:
            _translations[language] = {
                "name": LocaleStr(key="stream_reminders_event.name", version=eventData.version, title=eventData.title).translate(language),
                "description": LocaleStr(key=f"stream_reminders_event.description", youtube=YOUTUBE, twitch=TWITCH, youtube_url=HOYO_OFFICIAL_CHANNELS[eventData.game]["YouTube"], twitch_url=HOYO_OFFICIAL_CHANNELS[eventData.game]["Twitch"]).translate(language)
            }
        return _translations
    
    @classmethod
    async def _create_events(self, client: Zenox, event_data: EventReminder) -> tuple[int, int, int]:
        _success, _forbidden, _failed = 0, 0, 0
        GUILDS = [guild["id"] for guild in client.db.guilds.find({})]
        EVENT_IMAGE = open(f"./zenox-assets/assets/event-reminders/{event_data.image}", "+rb").read()
        _translations = self._pre_translate_schedule_stream(event_data)
        for guild in GUILDS:
            try:
                guild = GuildConfig(guild)
                
                if not guild.event_reminders[event_data.game].config["streams"]:
                    continue
                if not type(EVENT_IMAGE) == bytes or not EVENT_IMAGE:
                    EVENT_IMAGE = open(f"./zenox-assets/assets/event-reminders/{event_data.image}", "+rb").read()
                await client.get_guild(guild.id).create_scheduled_event(
                    name=_translations[guild.language]["name"],
                    description=_translations[guild.language]["description"],
                    start_time=event_data.start,
                    end_time=event_data.end,
                    location=HOYO_OFFICIAL_CHANNELS[event_data.game]["Twitch"],
                    image=EVENT_IMAGE,
                    entity_type=discord.EntityType.external,
                    privacy_level=discord.PrivacyLevel.guild_only
                )
                _success += 1
            except (discord.Forbidden):
                guild.updateGameConfigValue(event_data.game, EventReminderConfig, "streams", False)
                _forbidden += 1
            except Exception as e:
                client.capture_exception(e)
                _failed += 1
        return _success, _forbidden, _failed


async def setup(client: Zenox):
    await client.add_cog(Dev(client))