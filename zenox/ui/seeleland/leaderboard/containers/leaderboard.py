from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from zenox import ui
from zenox.l10n import LocaleStr

from zenox.clients.sl.formatting import format_category_label, format_crit_stats

from ..items.pagination import GoToLeaderboardButton, NextPageButton, PrevPageButton

if TYPE_CHECKING:
    from ..view import SeelelandLeaderboardView


class LeaderboardContainer(ui.DefaultContainer["SeelelandLeaderboardView"]):
    def __init__(self, view: SeelelandLeaderboardView) -> None:
        assert view.selected_char_id is not None
        assert view.selected_ctgr is not None
        assert view.rankings is not None

        char_name = view.hsr.get_character_name(int(view.selected_char_id), view.locale) or view.selected_char_id
        full_key = f"{view.selected_char_id}_{view.selected_ctgr}"
        category_label = format_category_label(view.hsr, full_key, view.locale)

        own_score = view.seele_data.leaderboard.get(full_key) if view.seele_data is not None else None

        total_entries = "?"

        def _split_rank(rank: str) -> tuple[str, str | None]:
            position, _, total = rank.partition("/")
            return position, (total or None)

        entry_lines: list[ui.TextDisplay] = []
        for entry in view.rankings.entries:
            score = entry.leaderboard.get(view.selected_ctgr)
            if score is None:
                continue

            position, total = _split_rank(score.rank)
            if total is not None:
                total_entries = total

            score_display = str(score.score)
            crit_suffix = format_crit_stats(score.crit_stats)
            if crit_suffix:
                score_display += f" - {crit_suffix}"

            entry_lines.append(
                ui.TextDisplay(
                    LocaleStr(
                        key="seeleland_lb.leaderboard.entry",
                        position=position,
                        name=entry.player.nm,
                        score=score_display,
                    )
                )
            )

        if own_score is not None:
            _, own_total = _split_rank(own_score.rank)
            if own_total is not None:
                total_entries = own_total

        children: list[ui.ActionRow | ui.TextDisplay | discord.ui.Separator] = [
            ui.TextDisplay(
                LocaleStr(
                    custom_str="# {title}\n{description}",
                    title=LocaleStr(
                        key="seeleland_lb.leaderboard.title",
                        character=char_name,
                        category=category_label,
                    ),
                    description=LocaleStr(
                        key="seeleland_lb.leaderboard.description", page=view.page, total=total_entries
                    ),
                )
            ),
            discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.small),
        ]

        if own_score is not None:
            own_position, _ = _split_rank(own_score.rank)
            name = view.selected.username if view.selected is not None else "You"
            own_score_display = str(own_score.sc)
            crit_suffix = format_crit_stats(own_score.crit_stats)
            if crit_suffix:
                own_score_display += f" - {crit_suffix}"
            children.append(
                ui.TextDisplay(
                    LocaleStr(
                        key="seeleland_lb.leaderboard.you",
                        percrank=own_score.percrank,
                        position=own_position,
                        name=name,
                        score=own_score_display,
                    )
                )
            )
            children.append(discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.small))

        if not entry_lines:
            children.append(ui.TextDisplay(LocaleStr(key="seeleland_lb.leaderboard.empty")))
        else:
            children.extend(entry_lines)

        children.append(discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.small))
        children.append(
            ui.ActionRow(
                PrevPageButton(disabled=view.page <= 1),
                NextPageButton(disabled=view.page >= 10 or len(view.rankings.entries) < 10),
                GoToLeaderboardButton(char_id=view.selected_char_id, ctgr=view.selected_ctgr, page=view.page),
            )
        )

        super().__init__(*children)
