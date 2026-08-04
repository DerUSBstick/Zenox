from __future__ import annotations

import logging
import random
import discord

from typing import TYPE_CHECKING

from zenox import ui
from zenox.embeds import DefaultEmbed, ErrorEmbed
from zenox.l10n import LocaleStr
from zenox.enums import Game
from zenox.emojis import get_game_emoji
from zenox.constants import (
    LINKING_IMAGE_GUIDE,
    ENKA_HOYO_TYPE_TO_GAME,
    ENKA_LINKING_GUIDE_IMAGE,
)
from zenox.db.classes import LinkingEntryTemplate, UserConfig
from .items.method import MethodSelector

if TYPE_CHECKING:
    from zenox.types import Interaction, User

__all__ = ("LinkingUI",)

logger = logging.getLogger(__name__)

_MAX_ACCOUNTS = 10
_SESSION_TTL_MINUTES = 15


class LinkingUI(ui.View):
    def __init__(self, *, author: User, locale: discord.Locale) -> None:
        super().__init__(author=author, locale=locale)
        self.add_item(MethodSelector())

    async def start(self, interaction: Interaction) -> None:
        embed = DefaultEmbed(
            self.locale,
            title=LocaleStr(key="linking.method.embed.title"),
            description=LocaleStr(key="linking.method.embed.description"),
        )
        await interaction.followup.send(embed=embed, view=self)

    # ------------------------------------------------------------------
    # UID linking flow
    # ------------------------------------------------------------------

    async def uid_linking(
        self, uid: str, game: Game, interaction: Interaction
    ) -> None:
        cache = interaction.client.linking_cache
        assert cache is not None

        is_linked = await cache.uid_is_already_linked(uid, game, interaction.user.id)
        if is_linked == 2:
            await self._send_error(
                interaction,
                title_key="linking.uid.already_linked.title",
                desc_key="linking.uid.already_linked.description",
            )
            return
        if is_linked == 1:
            await self._send_error(
                interaction,
                title_key="linking.uid.linked_to_other.title",
                desc_key="linking.uid.linked_to_other.description",
            )
            return

        if cache.get_linking_uids([(uid, game)]):
            await self._send_error(
                interaction,
                title_key="linking.uid.being_linked.title",
                desc_key="linking.uid.being_linked.description",
            )
            return

        user = await UserConfig.new(interaction.user.id)
        if len(user.accounts) >= _MAX_ACCOUNTS:
            await self._send_error(
                interaction,
                title_key="linking.max_accounts.title",
                desc_key="linking.max_accounts.description",
            )
            return

        entry = LinkingEntryTemplate(
            method="UID",
            hoyolab_id=None,
            data=[(uid, game)],
            user_id=interaction.user.id,
            started=discord.utils.utcnow(),
            code=random.randint(10000, 99999),
            interaction=interaction,
        )
        await cache.add_entry(entry)

        embed = DefaultEmbed(
            self.locale,
            title=LocaleStr(key="linking.uid.pending.title"),
            description=LocaleStr(key="linking.uid.pending.description"),
        )
        embed.add_field(
            name=LocaleStr(key="linking.uid.pending.uid_field"),
            value=f"{get_game_emoji(game)} `{uid}`",
        )
        embed.add_field(
            name=LocaleStr(key="linking.uid.pending.code_field"),
            value=f"```\n{entry.code}\n```",
        )
        expires_ts = int(entry.started.timestamp()) + _SESSION_TTL_MINUTES * 60
        embed.add_field(
            name=LocaleStr(key="linking.uid.pending.expires_field"),
            value=f"<t:{expires_ts}:R>",
        )
        if guide := LINKING_IMAGE_GUIDE.get(game):
            embed.set_image(url=guide)
        embed.set_footer(text=LocaleStr(key="linking.uid.pending.footer"))

        await self._absolute_edit(interaction, embed=embed, view=None)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_all_linked_embed(
        self,
        already_linked: list[tuple[str, Game]],
        linked_to_other: list[tuple[str, Game]],
        *,
        all_linked_title: str = "linking.hoyolab.all_linked.title",
        all_linked_desc: str = "linking.hoyolab.all_linked.description",
        already_linked_field: str = "linking.hoyolab.already_linked_field",
        linked_to_other_field: str = "linking.hoyolab.linked_to_other_field",
    ) -> discord.Embed:
        embed = ErrorEmbed(
            self.locale,
            title=LocaleStr(key=all_linked_title),
            description=LocaleStr(key=all_linked_desc),
        )
        if already_linked:
            embed.add_field(
                name=LocaleStr(key=already_linked_field),
                value="\n".join(f"{get_game_emoji(g)} `{u}`" for u, g in already_linked),
                inline=False,
            )
        if linked_to_other:
            embed.add_field(
                name=LocaleStr(key=linked_to_other_field),
                value="\n".join(f"{get_game_emoji(g)} `{u}`" for u, g in linked_to_other),
                inline=False,
            )
        return embed

    async def _send_error(
        self,
        interaction: Interaction,
        *,
        title_key: str,
        desc_key: str,
        desc_extras: dict | None = None,
    ) -> None:
        embed = ErrorEmbed(
            self.locale,
            title=LocaleStr(key=title_key),
            description=LocaleStr(key=desc_key, **(desc_extras or {})),
        )
        await self._absolute_edit(interaction, embed=embed, view=None)

    # ------------------------------------------------------------------
    # Enka linking flow
    # ------------------------------------------------------------------

    async def enka_linking(
        self, enka_username: str, interaction: Interaction
    ) -> None:
        cache = interaction.client.linking_cache
        assert cache is not None

        try:
            hoyos = await cache._linking_client.fetch_enka_hoyos(enka_username)
        except Exception:
            await self._send_error(
                interaction,
                title_key="linking.enka.api_error.title",
                desc_key="linking.enka.api_error.description",
            )
            return

        _supported_hoyo_types: frozenset[int] = frozenset(ENKA_HOYO_TYPE_TO_GAME)
        supported = [
            hoyo for hoyo in hoyos.values()
            if hoyo.get("hoyo_type") in _supported_hoyo_types
            and hoyo.get("verified")
            and hoyo.get("public")
        ]
        if not supported:
            await self._send_error(
                interaction,
                title_key="linking.enka.no_accounts.title",
                desc_key="linking.enka.no_accounts.description",
            )
            return

        already_linked: list[tuple[str, Game]] = []
        linked_to_other: list[tuple[str, Game]] = []
        pending: list[tuple[str, Game]] = []

        for hoyo in supported:
            uid = str(hoyo["uid"])
            game = ENKA_HOYO_TYPE_TO_GAME[hoyo["hoyo_type"]]
            status = await cache.uid_is_already_linked(uid, game, interaction.user.id)
            if status == 2:
                already_linked.append((uid, game))
            elif status == 1:
                linked_to_other.append((uid, game))
            else:
                pending.append((uid, game))

        in_progress = cache.get_linking_uids(pending)
        for pair in in_progress:
            pending.remove(pair)

        if not pending:
            embed = self._build_all_linked_embed(
                already_linked, linked_to_other,
                all_linked_title="linking.enka.all_linked.title",
                all_linked_desc="linking.enka.all_linked.description",
                already_linked_field="linking.enka.already_linked_field",
                linked_to_other_field="linking.enka.linked_to_other_field",
            )
            await self._absolute_edit(interaction, embed=embed, view=None)
            return

        user = await UserConfig.new(interaction.user.id)
        if len(user.accounts) + len(pending) > _MAX_ACCOUNTS:
            await self._send_error(
                interaction,
                title_key="linking.max_accounts.title",
                desc_key="linking.max_accounts.description",
            )
            return

        entry = LinkingEntryTemplate(
            method="Enka",
            hoyolab_id=None,
            enka_username=enka_username,
            data=pending,
            user_id=interaction.user.id,
            started=discord.utils.utcnow(),
            code=random.randint(10000, 99999),
            interaction=interaction,
        )
        await cache.add_entry(entry)

        embed = DefaultEmbed(
            self.locale,
            title=LocaleStr(key="linking.enka.pending.title"),
            description=LocaleStr(key="linking.enka.pending.description"),
        )
        embed.add_field(
            name=LocaleStr(key="linking.enka.pending.username_field"),
            value=f"`{enka_username}`",
        )
        embed.add_field(
            name=LocaleStr(key="linking.enka.pending.code_field"),
            value=f"```\n{entry.code}\n```",
        )
        expires_ts = int(entry.started.timestamp()) + _SESSION_TTL_MINUTES * 60
        embed.add_field(
            name=LocaleStr(key="linking.enka.pending.expires_field"),
            value=f"<t:{expires_ts}:R>",
        )
        embed.add_field(
            name=LocaleStr(key="linking.enka.pending.accounts_field"),
            value="\n".join(f"{get_game_emoji(g)} `{u}`" for u, g in pending),
            inline=False,
        )
        if ENKA_LINKING_GUIDE_IMAGE:
            embed.set_image(url=ENKA_LINKING_GUIDE_IMAGE)
        embed.set_footer(text=LocaleStr(key="linking.enka.pending.footer"))

        await self._absolute_edit(interaction, embed=embed, view=None)
