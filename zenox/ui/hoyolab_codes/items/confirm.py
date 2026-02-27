from __future__ import annotations

import discord
from typing import TYPE_CHECKING, Any

from zenox import emojis
from zenox.constants import ZENOX_LOCALES, HOYO_REDEEM_URLS, GAME_THUMBNAILS
from zenox.db.classes import Guild, SpecialProgram
from zenox.db.mongodb import DB
from zenox.embeds import Embed
from zenox.l10n import LocaleStr

from ...components import Button, View

if TYPE_CHECKING:
    from ..view import HoyolabCodesUI  # noqa: F401
    from ....types import Interaction


def _pre_translate(
    data: SpecialProgram,
) -> tuple[dict[discord.Locale, dict[str, str]], dict[discord.Locale, Embed], View]:
    """Pre-builds locale-keyed translations and embeds once before iterating guilds."""
    _translations: dict[discord.Locale, dict[str, str]] = {}
    _embeds: dict[discord.Locale, Embed] = {}
    _view = View(author=None, locale=discord.Locale.american_english)
    view_populated = False

    for language in ZENOX_LOCALES:
        content = LocaleStr(key="codes_notification.content", game_name=data.game.value).translate(language)
        direct_link = LocaleStr(key="codes_notification.direct_link").translate(language)

        if not data.codes:
            raise ValueError(f"No codes found for {data.game.value} version {data.version}")

        codes_str = "".join(
            f"> `{code.code}` | **[{direct_link}]({HOYO_REDEEM_URLS[data.game] + code.code})**\n"
            for code in data.codes
        )

        embed = Embed(
            locale=language,
            title=LocaleStr(key="stream_codes_message.embed.title", version=data.version),
            description=LocaleStr(
                key="stream_codes_message.embed.description",
                emj1=emojis.ANNOUNCEMENT,
                emj2=emojis.BLURPLE_LINK,
            ).translate(language),
        )
        embed.set_thumbnail(url=GAME_THUMBNAILS[data.game])
        embed.add_field(name=emojis.CODES1 + emojis.CODES2 + emojis.CODES3, value=codes_str)
        if data.stream_late_image:
            embed.set_image(url=data.stream_late_image)

        if not view_populated:
            for code in data.codes:
                _view.add_item(Button(label=code.code, url=HOYO_REDEEM_URLS[data.game] + code.code))
            view_populated = True

        _translations[language] = {"content": content}
        _embeds[language] = embed

    return _translations, _embeds, _view


class ConfirmButton(Button["HoyolabCodesUI"]):
    def __init__(self):
        super().__init__(
            label="Confirm",
            style=discord.ButtonStyle.success
        )

    async def callback(self, i: Interaction) -> Any:
        if not i.response.is_done():
            await i.response.defer(ephemeral=True)

        translations, embeds, view = _pre_translate(self.view.data)

        if self.view.action == "Global":
            await self.view.data._update_val("codes_published", True)
            await self._publish_globally(i, translations, embeds, view)
        elif self.view.action in ("Dev", "Guild"):
            assert self.view.guild_id is not None
            success = await self._publish_to_guild(i, self.view.guild_id, translations, embeds, view)
            if not success:
                await self.view.data._update_val("codes_published", False)
                await i.followup.send("Guild is not eligible (no codes channel configured for this game).", ephemeral=True)
                return

        assert i.client.db_config is not None
        await self.view.update_message(i)

        await i.followup.send(f"Published to **{self.view.action}**.", ephemeral=True)

    async def _publish_to_guild(
        self,
        i: Interaction,
        guild_id: int,
        translations: dict[discord.Locale, dict[str, str]],
        embeds: dict[discord.Locale, Embed],
        view: View,
        *,
        guild_verified: bool = False,
    ) -> bool:
        """Sends stream codes to a single guild's configured codes channel.
        Returns True if the guild qualified and the message was sent.
        Pass guild_verified=True to skip the eligibility DB check (e.g. when already filtered globally)."""
        game = self.view.data.game

        if not guild_verified:
            guild_data = await DB.guilds.find_one(
                {"id": guild_id, f"codes.{game.value}.channel": {"$ne": None}},
                {"_id": 0, "id": 1},
            )
            if not guild_data:
                return False

        guild = await Guild.new(guild_id)
        channel_id = guild.codes[game].channel
        if channel_id is None:
            return False

        channel = i.client.get_channel(channel_id) or await i.client.fetch_channel(channel_id)
        if not channel or not isinstance(channel, discord.TextChannel):
            return False

        role = None
        role_id = guild.codes[game].mention_role
        if role_id is not None:
            guild_obj = i.client.get_guild(guild_id) or await i.client.fetch_guild(guild_id)
            role = guild_obj.get_role(role_id)

        send_msg = (
            f"{role.mention + ' ' if role is not None else ''}"
            f"{'@everyone ' if guild.codes[game].mention_everyone else ''}"
            f"{translations[guild.language]['content']}"
        )
        await channel.send(send_msg, embed=embeds[guild.language], view=view)
        return True

    async def _publish_globally(
        self,
        i: Interaction,
        translations: dict[discord.Locale, dict[str, str]],
        embeds: dict[discord.Locale, Embed],
        view: View,
    ) -> None:
        """Sends stream codes to all guilds that have a codes channel configured for this game."""
        game = self.view.data.game

        cursor = DB.guilds.find(
            {f"codes.{game.value}.channel": {"$ne": None}},
            {"_id": 0, "id": 1},
        )
        async for guild_data in cursor:
            try:
                await self._publish_to_guild(i, guild_data["id"], translations, embeds, view, guild_verified=True)
            except Exception as e:
                i.client.capture_exception(e)