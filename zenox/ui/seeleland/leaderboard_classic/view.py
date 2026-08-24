from __future__ import annotations

from typing import TYPE_CHECKING

from zenox import ui
from zenox.clients.sl.constants import SEELELAND_TEAM_NAMES
from zenox.clients.sl.formatting import format_crit_stats, parse_category_key
from zenox.embeds import DefaultEmbed
from zenox.l10n import LocaleStr, translator

from .items import (
    FirstPageButton,
    GoToLeaderboardButton,
    LastPageButton,
    NextPageButton,
    PrevPageButton,
    ShowLeaderboardDetailsButton,
)

if TYPE_CHECKING:
    import discord

    from zenox.clients.sl import RankingsResponse, SeelelandLeaderboardData, SLClient
    from zenox.clients.store.hsr import HSRStore
    from zenox.types import Interaction, User

ENKA_ASSET_BASE = "https://enka.network"


class SeelelandClassicPaginatorView(ui.View):
    """Plain ``View`` + ``Embed`` leaderboard paginator (A/B alternative to the
    LayoutView-based ``ui/seeleland/leaderboard``), shared by ``/sl2`` and
    ``/sl3`` - they only differ in how they resolve ``char_id``/``ctgr``
    before constructing this view.
    """

    def __init__(
        self,
        *,
        author: User,
        locale: discord.Locale,
        sl: SLClient,
        hsr: HSRStore,
        char_id: str,
        ctgr: str,
        rankings: RankingsResponse,
        highlight_uid: str | None = None,
        highlight_name: str | None = None,
        highlight_score: SeelelandLeaderboardData | None = None,
    ) -> None:
        super().__init__(author=author, locale=locale)

        self.sl = sl
        self.hsr = hsr
        self.char_id = char_id
        self.ctgr = ctgr
        self.page = rankings.page
        self.rankings = rankings
        self.highlight_uid = highlight_uid
        self.highlight_name = highlight_name
        self.highlight_score = highlight_score

    def _build_items(self) -> None:
        self.clear_items()
        self.add_item(FirstPageButton(disabled=self.page <= 1))
        self.add_item(PrevPageButton(disabled=self.page <= 1))
        self.add_item(NextPageButton(disabled=self.page >= 10 or len(self.rankings.entries) < 10))
        self.add_item(LastPageButton(disabled=self.page >= 10))
        self.add_item(ShowLeaderboardDetailsButton())
        self.add_item(GoToLeaderboardButton(char_id=self.char_id, ctgr=self.ctgr, page=self.page))

    @staticmethod
    def _split_rank(rank: str) -> tuple[str, str | None]:
        """Split a ``"N/total"`` rank string into ``("N", "total")``."""
        position, _, total = rank.partition("/")
        return position, (total or None)

    def _build_embed(self) -> DefaultEmbed:
        full_key = f"{self.char_id}_{self.ctgr}"
        key = parse_category_key(full_key)

        char_name = self.hsr.get_character_name(int(self.char_id), self.locale) or self.char_id
        character = self.hsr.get_character(int(self.char_id))

        if key is not None:
            light_cone = self.hsr.get_light_cone(key.light_cone_id)
            lc_name = self.hsr.get_light_cone_name(key.light_cone_id, self.locale) or str(key.light_cone_id)
            team_name = SEELELAND_TEAM_NAMES.get(key.team_code, key.team_code) if key.team_code else None
            base_label = translator.translate(LocaleStr(key="seeleland_lb.classic.base_speed"), self.locale)
            speed_label = f"Spd {key.speed}" if key.speed else base_label
            title_parts = [part for part in (key.bracket, team_name, speed_label) if part]
            title = " · ".join(title_parts) if title_parts else char_name
        else:
            light_cone = None
            lc_name = None
            title = full_key

        embed = DefaultEmbed(self.locale, title=title)

        if lc_name is not None:
            icon_url = f"{ENKA_ASSET_BASE}{light_cone.icon_path}" if light_cone is not None else None
            embed.set_author(name=lc_name, icon_url=icon_url)
        if character is not None:
            embed.set_thumbnail(url=f"{ENKA_ASSET_BASE}{character.cutin_icon}")

        lines: list[str] = []
        total_entries: str | None = None

        if self.highlight_score is not None:
            position, total = self._split_rank(self.highlight_score.rank)
            total_entries = total_entries or total
            crit_suffix = format_crit_stats(self.highlight_score.crit_stats)
            lines.append(
                translator.translate(
                    LocaleStr(key="seeleland_lb.classic.you_header", percrank=self.highlight_score.percrank),
                    self.locale,
                )
            )
            you_name = self.highlight_name or translator.translate(
                LocaleStr(key="seeleland_lb.classic.you_label"), self.locale
            )
            you_line = f"{position}. **{you_name}** - **{self.highlight_score.sc}**"
            if crit_suffix:
                you_line += f" - {crit_suffix}"
            lines.append(you_line)
            lines.append("---")
        elif self.highlight_uid is not None and self.highlight_name is not None:
            lines.append(
                translator.translate(
                    LocaleStr(
                        key="seeleland_lb.classic.no_rank_found",
                        name=self.highlight_name or "?",
                        uid=self.highlight_uid,
                    ),
                    self.locale,
                )
            )
            lines.append("---")

        if not self.rankings.entries:
            lines.append(translator.translate(LocaleStr(key="seeleland_lb.leaderboard.empty"), self.locale))
        else:
            for entry in self.rankings.entries:
                score = entry.leaderboard.get(self.ctgr)
                if score is None:
                    continue

                position, total = self._split_rank(score.rank)
                total_entries = total_entries or total

                is_own = self.highlight_uid is not None and entry.player.id == self.highlight_uid
                name = f"**{entry.player.nm}**" if is_own else entry.player.nm

                entry_line = f"{position}. {name} - **{score.score}**"
                crit_suffix = format_crit_stats(score.crit_stats)
                if crit_suffix:
                    entry_line += f" - {crit_suffix}"

                lines.append(entry_line)

        embed.description = "\n".join(lines)

        if total_entries is not None:
            embed.set_footer(text=f"Total entries: {total_entries}")

        return embed

    def build_details_embed(self) -> DefaultEmbed:
        """Build an ephemeral "leaderboard details" embed decoding the raw
        category key into its component parts.
        """
        full_key = f"{self.char_id}_{self.ctgr}"
        key = parse_category_key(full_key)

        char_name = self.hsr.get_character_name(int(self.char_id), self.locale) or self.char_id
        embed = DefaultEmbed(self.locale, title=LocaleStr(key="seeleland_lb.classic.details_title"))
        embed.add_field(name=LocaleStr(key="seeleland_lb.classic.details.character_field"), value=char_name, inline=True)

        if key is not None:
            lc_name = self.hsr.get_light_cone_name(key.light_cone_id, self.locale) or str(key.light_cone_id)
            team_name = (
                SEELELAND_TEAM_NAMES.get(key.team_code, key.team_code)
                if key.team_code
                else translator.translate(LocaleStr(key="seeleland_lb.classic.no_variant"), self.locale)
            )
            speed_value = key.speed or translator.translate(LocaleStr(key="seeleland_lb.classic.base_speed"), self.locale)
            embed.add_field(name=LocaleStr(key="seeleland_lb.classic.details.light_cone_field"), value=lc_name, inline=True)
            embed.add_field(name=LocaleStr(key="seeleland_lb.classic.details.bracket_field"), value=key.bracket, inline=True)
            embed.add_field(name=LocaleStr(key="seeleland_lb.classic.details.variant_field"), value=team_name, inline=True)
            embed.add_field(name=LocaleStr(key="seeleland_lb.classic.details.speed_field"), value=speed_value, inline=True)

        embed.add_field(
            name=LocaleStr(key="seeleland_lb.classic.details.category_key_field"), value=f"`{self.ctgr}`", inline=False
        )
        return embed

    async def start(self, interaction: Interaction) -> None:
        self._build_items()
        embed = self._build_embed()

        if not interaction.response.is_done():
            await interaction.response.send_message(embed=embed, view=self)
        else:
            await interaction.followup.send(embed=embed, view=self)

        self.message = await interaction.original_response()

    async def refresh(self, interaction: Interaction) -> None:
        self._build_items()
        embed = self._build_embed()
        await interaction.response.edit_message(embed=embed, view=self)
