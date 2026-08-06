from __future__ import annotations

import re
from discord import app_commands
from discord.app_commands import locale_str
from discord.ext import commands
from typing import TYPE_CHECKING

# from ..ui.seele.view import SeeleView
from ..ui.seeleland.leaderboard.view import SeelelandLeaderboardView
from ..ui.seeleland.leaderboard_classic.view import SeelelandClassicPaginatorView
from ..clients.sl import SLClient
from ..clients.sl.constants import SEELELAND_TEAM_NAMES
from ..clients.sl.leaderboards_catalog import (
    SEELELAND_LEADERBOARDS_CATALOG,
    get_catalog_brackets,
    get_catalog_entries_for_bracket,
)
from ..constants import Game, SEELELAND_REGEX
from ..db.classes import GameAccount, UserConfig
from ..exceptions import InvalidInputError

from zenox.l10n import LocaleStr
from zenox.embeds import DefaultEmbed

if TYPE_CHECKING:
    from ..bot import Zenox
    from ..clients.sl import SeelelandLeaderboardData
    from ..types import Interaction


class Seele(commands.Cog):
    def __init__(self, client: Zenox):
        self.client = client

    @app_commands.command(
        name=locale_str("sl"),
        description=locale_str(
            "View how you rank on Seeleland's leaderboards", key="sl_command.description"
        ),
    )
    @app_commands.user_install()
    @app_commands.guild_install()
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def sl_command(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=False)

        user = await UserConfig.new(interaction.user.id)

        # If not any user linked game account is hsr
        if not any(account for account in user.accounts if account.game == "Honkai: Star Rail"):
            embed = DefaultEmbed(
                locale=user.language,
                title=LocaleStr(key="sl_command.no_account.title"),
                description=LocaleStr(key="sl_command.no_account.description"),
            )
            await interaction.followup.send(embed=embed)
            return

        # view = SeeleView(
        #     author=interaction.user,
        #     user=user,
        #     locale=user.language
        # )
        # await view.start(interaction)

        view = SeelelandLeaderboardView(
            author=interaction.user,
            locale=user.language,
            user=user,
            client=interaction.client,
        )
        await view.update(interaction)

    # ------------------------------------------------------------------ #
    # Shared helpers for the /sl2 and /sl3 A/B test commands              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _starrail_accounts(user: UserConfig) -> list[GameAccount]:
        return [account for account in user.accounts if account.game == Game.STARRAIL]

    def _resolve_account_uid(self, user: UserConfig, requested_uid: str | None) -> str | None:
        """Resolve which uid to use: the requested one if it's actually one of the
        user's linked Star Rail accounts, otherwise their first linked account.
        """
        starrail_accounts = self._starrail_accounts(user)
        if requested_uid and any(account.uid == requested_uid for account in starrail_accounts):
            return requested_uid
        return starrail_accounts[0].uid if starrail_accounts else None

    @staticmethod
    def _error_choice(message: str) -> list[app_commands.Choice[str]]:
        return [app_commands.Choice(name=message[:100], value="none")]

    @staticmethod
    def _matching(choices: list[app_commands.Choice[str]], current: str) -> list[app_commands.Choice[str]]:
        return [choice for choice in choices if current.lower() in choice.name.lower()][:25]

    @staticmethod
    async def _resolve_highlight(
        sl: SLClient, uid: str | None, char_id: str, ctgr: str, requested_by: int
    ) -> tuple[str | None, SeelelandLeaderboardData | None]:
        """Fetch the highlighted account's own display name + leaderboard score
        for this exact category, independent of which page is currently shown.
        """
        if uid is None:
            return None, None

        seele_data = await sl.get_player_data(uid, requested_by=requested_by)
        return seele_data.account.nm, seele_data.leaderboard.get(f"{char_id}_{ctgr}")

    # ------------------------------------------------------------------ #
    # /sl2 - account-driven autocomplete (reuses SLClient.get_player_data) #
    # ------------------------------------------------------------------ #

    @app_commands.command(
        name=locale_str("sl2"),
        description=locale_str(
            "(A/B test) View Seeleland leaderboards, filters chosen before running the command",
            key="sl2_command.description",
        ),
    )
    @app_commands.describe(
        character=locale_str("Character to view the leaderboard for", key="sl2_command.character_param_desc"),
        leaderboard=locale_str(
            "Eidolon/Superimposition bracket, e.g. E0S5", key="sl2_command.leaderboard_param_desc"
        ),
        weapon=locale_str("Light cone to view the leaderboard for", key="sl2_command.weapon_param_desc"),
        variant=locale_str(
            "Team/build variant, defaults to none", key="sl2_command.variant_param_desc"
        ),
        speed=locale_str(
            "Speed breakpoint, defaults to Base", key="sl2_command.speed_param_desc"
        ),
        account=locale_str(
            "Account to browse/highlight, defaults to your first linked Star Rail account",
            key="sl2_command.account_param_desc",
        ),
    )
    @app_commands.user_install()
    @app_commands.guild_install()
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def sl2_command(
        self,
        interaction: Interaction,
        character: str,
        leaderboard: str,
        weapon: str,
        variant: str | None = None,
        speed: str | None = None,
        account: str | None = None,
    ) -> None:
        if character == "none" or leaderboard == "none" or weapon == "none" or not weapon.isdigit():
            raise InvalidInputError(LocaleStr(key="seeleland_lb.invalid_selection", field="character/leaderboard/weapon"))

        await interaction.response.defer(ephemeral=False)

        user = await UserConfig.new(interaction.user.id)
        uid = self._resolve_account_uid(user, account)
        if uid is None:
            embed = DefaultEmbed(
                locale=user.language,
                title=LocaleStr(key="sl_command.no_account.title"),
                description=LocaleStr(key="sl_command.no_account.description"),
            )
            await interaction.followup.send(embed=embed)
            return

        team_code = "" if not variant or variant == "none" else variant
        speed_suffix = "" if not speed or speed == "Base" or speed == "none" else f"_{speed}"
        ctgr = f"{leaderboard}_{weapon}{team_code}{speed_suffix}"

        sl = SLClient(interaction.client)
        rankings = await sl.get_rankings(character, ctgr, 1, requested_by=interaction.user.id)
        highlight_name, highlight_score = await self._resolve_highlight(
            sl, uid, character, ctgr, interaction.user.id
        )

        view = SeelelandClassicPaginatorView(
            author=interaction.user,
            locale=user.language,
            sl=sl,
            hsr=interaction.client.store.hsr,
            char_id=character,
            ctgr=ctgr,
            rankings=rankings,
            highlight_uid=uid,
            highlight_name=highlight_name,
            highlight_score=highlight_score,
        )
        await view.start(interaction)

    @sl2_command.autocomplete("character")
    async def sl2_character_autocomplete(self, interaction: Interaction, current: str) -> list[app_commands.Choice[str]]:
        try:
            user = await UserConfig.new(interaction.user.id)
            uid = self._resolve_account_uid(user, interaction.namespace.account)
            if uid is None:
                return self._error_choice("Link a Star Rail account first")

            sl = SLClient(interaction.client)
            seele_data = await sl.get_player_data(uid, requested_by=interaction.user.id)
            hsr = interaction.client.store.hsr

            char_ids: dict[str, None] = {}
            for key in seele_data.leaderboard:
                match = re.match(SEELELAND_REGEX, key)
                if match is None:
                    continue
                char_id = match.group(1)
                if hsr.get_character(int(char_id)) is None:
                    continue
                char_ids.setdefault(char_id, None)

            choices = [
                app_commands.Choice(name=hsr.get_character_name(int(char_id), interaction.locale) or char_id, value=char_id)
                for char_id in char_ids
            ]
        except Exception:
            return self._error_choice("Could not load characters")

        return self._matching(choices, current)

    @sl2_command.autocomplete("leaderboard")
    async def sl2_leaderboard_autocomplete(self, interaction: Interaction, current: str) -> list[app_commands.Choice[str]]:
        try:
            char_id = interaction.namespace.character
            if not char_id or char_id == "none":
                return self._error_choice("Select a character first")

            user = await UserConfig.new(interaction.user.id)
            uid = self._resolve_account_uid(user, interaction.namespace.account)
            if uid is None:
                return self._error_choice("Link a Star Rail account first")

            sl = SLClient(interaction.client)
            seele_data = await sl.get_player_data(uid, requested_by=interaction.user.id)

            prefix = f"{char_id}_"
            brackets: dict[str, None] = {}
            for key in seele_data.leaderboard:
                if not key.startswith(prefix):
                    continue
                match = re.match(SEELELAND_REGEX, key)
                if match is None:
                    continue
                brackets.setdefault(match.group(2), None)

            choices = [app_commands.Choice(name=bracket, value=bracket) for bracket in brackets]
        except Exception:
            return self._error_choice("Could not load leaderboards")

        return self._matching(choices, current)

    @sl2_command.autocomplete("weapon")
    async def sl2_weapon_autocomplete(self, interaction: Interaction, current: str) -> list[app_commands.Choice[str]]:
        try:
            char_id = interaction.namespace.character
            bracket = interaction.namespace.leaderboard
            if not char_id or char_id == "none" or not bracket or bracket == "none":
                return self._error_choice("Select a character and leaderboard first")

            user = await UserConfig.new(interaction.user.id)
            uid = self._resolve_account_uid(user, interaction.namespace.account)
            if uid is None:
                return self._error_choice("Link a Star Rail account first")

            sl = SLClient(interaction.client)
            seele_data = await sl.get_player_data(uid, requested_by=interaction.user.id)
            hsr = interaction.client.store.hsr

            prefix = f"{char_id}_{bracket}_"
            lc_ids: dict[str, None] = {}
            for key in seele_data.leaderboard:
                if not key.startswith(prefix):
                    continue
                match = re.match(SEELELAND_REGEX, key)
                if match is None:
                    continue
                lc_ids.setdefault(match.group(3), None)

            choices = [
                app_commands.Choice(name=hsr.get_light_cone_name(int(lc_id), interaction.locale) or lc_id, value=lc_id)
                for lc_id in lc_ids
            ]
        except Exception:
            return self._error_choice("Could not load weapons")

        return self._matching(choices, current)

    @sl2_command.autocomplete("variant")
    async def sl2_variant_autocomplete(self, interaction: Interaction, current: str) -> list[app_commands.Choice[str]]:
        try:
            char_id = interaction.namespace.character
            bracket = interaction.namespace.leaderboard
            weapon = interaction.namespace.weapon
            if not char_id or char_id == "none" or not bracket or bracket == "none" or not weapon or weapon == "none":
                return self._error_choice("Select a character, leaderboard and weapon first")

            user = await UserConfig.new(interaction.user.id)
            uid = self._resolve_account_uid(user, interaction.namespace.account)
            if uid is None:
                return self._error_choice("Link a Star Rail account first")

            sl = SLClient(interaction.client)
            seele_data = await sl.get_player_data(uid, requested_by=interaction.user.id)

            prefix = f"{char_id}_{bracket}_{weapon}"
            teams: dict[str, None] = {}
            for key in seele_data.leaderboard:
                if not key.startswith(prefix):
                    continue
                match = re.match(SEELELAND_REGEX, key)
                if match is None:
                    continue
                teams.setdefault(match.group(4) or "none", None)

            choices = [
                app_commands.Choice(name="No team" if team == "none" else SEELELAND_TEAM_NAMES.get(team, team), value=team)
                for team in teams
            ]
        except Exception:
            return self._error_choice("Could not load variants")

        return self._matching(choices, current)

    @sl2_command.autocomplete("speed")
    async def sl2_speed_autocomplete(self, interaction: Interaction, current: str) -> list[app_commands.Choice[str]]:
        try:
            char_id = interaction.namespace.character
            bracket = interaction.namespace.leaderboard
            weapon = interaction.namespace.weapon
            if not char_id or char_id == "none" or not bracket or bracket == "none" or not weapon or weapon == "none":
                return self._error_choice("Select a character, leaderboard and weapon first")

            user = await UserConfig.new(interaction.user.id)
            uid = self._resolve_account_uid(user, interaction.namespace.account)
            if uid is None:
                return self._error_choice("Link a Star Rail account first")

            variant = interaction.namespace.variant
            team_code = "" if not variant or variant in ("none", "no_team") else variant

            sl = SLClient(interaction.client)
            seele_data = await sl.get_player_data(uid, requested_by=interaction.user.id)

            prefix = f"{char_id}_{bracket}_{weapon}{team_code}"
            speeds: dict[str, None] = {}
            for key in seele_data.leaderboard:
                if not key.startswith(prefix):
                    continue
                match = re.match(SEELELAND_REGEX, key)
                if match is None or match.group(4) != team_code:
                    continue
                speeds.setdefault(match.group(5) or "Base", None)

            choices = [app_commands.Choice(name=speed, value=speed) for speed in speeds]
        except Exception:
            return self._error_choice("Could not load speed breakpoints")

        return self._matching(choices, current)

    # ------------------------------------------------------------------ #
    # /sl3 - static-catalog-driven autocomplete (no account required)     #
    # ------------------------------------------------------------------ #

    @app_commands.command(
        name=locale_str("sl3"),
        description=locale_str(
            "(A/B test) View Seeleland leaderboards, browsing all characters/light cones (not account-scoped)",
            key="sl3_command.description",
        ),
    )
    @app_commands.describe(
        character=locale_str("Character to view the leaderboard for", key="sl3_command.character_param_desc"),
        leaderboard=locale_str(
            "Eidolon/Superimposition bracket, e.g. E0S5", key="sl3_command.leaderboard_param_desc"
        ),
        weapon=locale_str("Light cone to view the leaderboard for", key="sl3_command.weapon_param_desc"),
        variant=locale_str(
            "Team/build variant override, defaults to this weapon's featured build",
            key="sl3_command.variant_param_desc",
        ),
        speed=locale_str(
            "Speed breakpoint override, defaults to this weapon's featured build",
            key="sl3_command.speed_param_desc",
        ),
        account=locale_str(
            "Account to highlight your own rank, if you're on this leaderboard",
            key="sl3_command.account_param_desc",
        ),
    )
    @app_commands.user_install()
    @app_commands.guild_install()
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def sl3_command(
        self,
        interaction: Interaction,
        character: str,
        leaderboard: str,
        weapon: str,
        variant: str | None = None,
        speed: str | None = None,
        account: str | None = None,
    ) -> None:
        if character == "none" or leaderboard == "none" or weapon == "none" or not weapon.isdigit():
            raise InvalidInputError(LocaleStr(key="seeleland_lb.invalid_selection", field="character/leaderboard/weapon"))

        entries = get_catalog_entries_for_bracket(character, leaderboard)
        entry = next((entry for entry in entries if str(entry.light_cone_id) == weapon), None)
        if entry is None:
            raise InvalidInputError(LocaleStr(key="seeleland_lb.no_leaderboard_found"))

        await interaction.response.defer(ephemeral=False)

        user = await UserConfig.new(interaction.user.id)
        uid = self._resolve_account_uid(user, account)

        base_ctgr = entry.resolve_ctgr()
        if variant or speed:
            match = re.match(SEELELAND_REGEX, f"{character}_{base_ctgr}")
            if match is not None:
                _, bracket, lc_id, existing_team, existing_speed = match.groups()
                team_code = existing_team if not variant or variant == "none" else variant
                speed_value = existing_speed if not speed or speed == "none" else speed
                speed_value = None if speed_value == "Base" else speed_value
                base_ctgr = f"{bracket}_{lc_id}{team_code}" + (f"_{speed_value}" if speed_value else "")

        ctgr = base_ctgr
        sl = SLClient(interaction.client)
        rankings = await sl.get_rankings(character, ctgr, 1, requested_by=interaction.user.id)
        highlight_name, highlight_score = await self._resolve_highlight(
            sl, uid, character, ctgr, interaction.user.id
        )

        view = SeelelandClassicPaginatorView(
            author=interaction.user,
            locale=user.language,
            sl=sl,
            hsr=interaction.client.store.hsr,
            char_id=character,
            ctgr=ctgr,
            rankings=rankings,
            highlight_uid=uid,
            highlight_name=highlight_name,
            highlight_score=highlight_score,
        )
        await view.start(interaction)

    @sl3_command.autocomplete("character")
    async def sl3_character_autocomplete(self, interaction: Interaction, current: str) -> list[app_commands.Choice[str]]:
        hsr = interaction.client.store.hsr
        choices = [
            app_commands.Choice(name=hsr.get_character_name(int(char_id), interaction.locale) or char_id, value=char_id)
            for char_id in SEELELAND_LEADERBOARDS_CATALOG
        ]
        return self._matching(choices, current)

    @sl3_command.autocomplete("leaderboard")
    async def sl3_leaderboard_autocomplete(self, interaction: Interaction, current: str) -> list[app_commands.Choice[str]]:
        char_id = interaction.namespace.character
        if not char_id or char_id == "none":
            return self._error_choice("Select a character first")

        brackets = get_catalog_brackets(char_id)
        choices = [app_commands.Choice(name=bracket, value=bracket) for bracket in brackets]
        return self._matching(choices, current)

    @sl3_command.autocomplete("weapon")
    async def sl3_weapon_autocomplete(self, interaction: Interaction, current: str) -> list[app_commands.Choice[str]]:
        char_id = interaction.namespace.character
        bracket = interaction.namespace.leaderboard
        if not char_id or char_id == "none" or not bracket or bracket == "none":
            return self._error_choice("Select a character and leaderboard first")

        hsr = interaction.client.store.hsr
        entries = get_catalog_entries_for_bracket(char_id, bracket)
        choices = [
            app_commands.Choice(
                name=hsr.get_light_cone_name(entry.light_cone_id, interaction.locale) or str(entry.light_cone_id),
                value=str(entry.light_cone_id),
            )
            for entry in entries
        ]
        return self._matching(choices, current)

    @sl3_command.autocomplete("variant")
    async def sl3_variant_autocomplete(self, interaction: Interaction, current: str) -> list[app_commands.Choice[str]]:
        char_id = interaction.namespace.character
        bracket = interaction.namespace.leaderboard
        weapon = interaction.namespace.weapon
        if not char_id or char_id == "none" or not bracket or bracket == "none" or not weapon or weapon == "none":
            return self._error_choice("Select a character, leaderboard and weapon first")

        entries = get_catalog_entries_for_bracket(char_id, bracket)
        entry = next((entry for entry in entries if str(entry.light_cone_id) == weapon), None)
        if entry is None:
            return self._error_choice("Select a valid weapon first")

        match = re.match(SEELELAND_REGEX, f"{char_id}_{entry.resolve_ctgr()}")
        team_code = match.group(4) if match else ""

        choices = [
            app_commands.Choice(
                name="No team" if not team_code else SEELELAND_TEAM_NAMES.get(team_code, team_code),
                value=team_code or "none",
            )
        ]
        return self._matching(choices, current)

    @sl3_command.autocomplete("speed")
    async def sl3_speed_autocomplete(self, interaction: Interaction, current: str) -> list[app_commands.Choice[str]]:
        char_id = interaction.namespace.character
        bracket = interaction.namespace.leaderboard
        weapon = interaction.namespace.weapon
        if not char_id or char_id == "none" or not bracket or bracket == "none" or not weapon or weapon == "none":
            return self._error_choice("Select a character, leaderboard and weapon first")

        entries = get_catalog_entries_for_bracket(char_id, bracket)
        entry = next((entry for entry in entries if str(entry.light_cone_id) == weapon), None)
        if entry is None:
            return self._error_choice("Select a valid weapon first")

        match = re.match(SEELELAND_REGEX, f"{char_id}_{entry.resolve_ctgr()}")
        speed = (match.group(5) if match else None) or "Base"

        choices = [app_commands.Choice(name=speed, value=speed)]
        return self._matching(choices, current)

    @sl2_command.autocomplete("account")
    @sl3_command.autocomplete("account")
    async def sl_account_autocomplete(self, interaction: Interaction, current: str) -> list[app_commands.Choice[str]]:
        user = await UserConfig.new(interaction.user.id)
        choices = [
            app_commands.Choice(name=f"{account.username} ({account.uid})", value=account.uid)
            for account in self._starrail_accounts(user)
        ]
        return self._matching(choices, current)


async def setup(client: Zenox) -> None:
    await client.add_cog(Seele(client))
