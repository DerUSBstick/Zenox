"""Honkai: Star Rail data store, backed by api.enka.network."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import ClassVar

import aiohttp
import discord

from zenox.clients.store.base import GameStore

from .models import (
    HSRCharacter,
    HSREidolon,
    HSRLightCone,
    HSRProfileIcon,
    HSRRelicPiece,
    HSRSkillNode,
    RelicAffixValue,
)

__all__ = ("HSRStore",)


class HSRStore(GameStore):
    """Honkai: Star Rail game data store.

    Call ``await warm_up(session)`` once (done automatically by ``Store.warm_up``
    during the bot's ``setup_hook``) before using any of the accessors below.
    """

    BASE_URL: ClassVar[str] = "https://api.enka.network/store/hsr/"
    CACHE_DIR: ClassVar[Path] = Path("./cache/store/hsr")
    TEXT_MAP_FILE: ClassVar[str] = "hsr.json"

    # Only the files we actually need. The superseded honker_characters.json,
    # honker_weps.json, honker_relics.json, honker_skilltree.json, honker_ranks.json
    # and honker_meta.json duplicates are intentionally not fetched: live-data
    # verification confirmed the non-honker files (ranks.json, pfps.json, etc.)
    # are already correct/canonical on their own.
    FILES: ClassVar[tuple[str, ...]] = (
        "avatars.json",
        "weapons.json",
        "relics.json",
        "affixes.json",
        "skills.json",
        "tree.json",
        "ranks.json",
        "pfps.json",
        "hsr.json",
    )

    def __init__(self) -> None:
        super().__init__()
        self._characters: dict[int, HSRCharacter] = {}
        self._light_cones: dict[int, HSRLightCone] = {}
        self._relics: dict[int, HSRRelicPiece] = {}
        self._skill_nodes: dict[int, HSRSkillNode] = {}
        self._eidolons: dict[int, HSREidolon] = {}
        self._profile_icons: dict[int, HSRProfileIcon] = {}

    async def warm_up(self, session: aiohttp.ClientSession) -> None:
        """Fetch every required file in parallel and build the typed caches."""
        await asyncio.gather(*(self._fetch_json(session, f) for f in self.FILES))

        self._build_characters()
        self._build_light_cones()
        self._build_relics()
        self._build_skill_nodes()
        self._build_eidolons()
        self._build_profile_icons()

    # ------------------------------------------------------------------ #
    # Cache builders                                                      #
    # ------------------------------------------------------------------ #

    def _build_characters(self) -> None:
        avatars = self._raw["avatars.json"]
        self._characters = {
            int(char_id): HSRCharacter.from_raw(int(char_id), data)
            for char_id, data in avatars.items()
        }

    def _build_light_cones(self) -> None:
        weapons = self._raw["weapons.json"]
        self._light_cones = {
            int(lc_id): HSRLightCone.from_raw(int(lc_id), data)
            for lc_id, data in weapons.items()
        }

    def _build_relics(self) -> None:
        relics = self._raw["relics.json"]["Items"]
        self._relics = {
            int(relic_id): HSRRelicPiece.from_raw(int(relic_id), data)
            for relic_id, data in relics.items()
        }

    def _build_skill_nodes(self) -> None:
        skills = self._raw["skills.json"]
        props = self._raw["tree.json"]
        self._skill_nodes = {
            int(node_id): HSRSkillNode.from_raw(int(node_id), data, props.get(node_id))
            for node_id, data in skills.items()
        }

    def _build_eidolons(self) -> None:
        ranks = self._raw["ranks.json"]
        self._eidolons = {
            int(rank_id): HSREidolon.from_raw(int(rank_id), data) for rank_id, data in ranks.items()
        }

    def _build_profile_icons(self) -> None:
        pfps = self._raw["pfps.json"]
        self._profile_icons = {
            int(icon_id): HSRProfileIcon.from_raw(int(icon_id), data) for icon_id, data in pfps.items()
        }

    # ------------------------------------------------------------------ #
    # Accessors                                                           #
    # ------------------------------------------------------------------ #

    @property
    def characters(self) -> dict[int, HSRCharacter]:
        return self._characters

    def get_character(self, char_id: int) -> HSRCharacter | None:
        return self._characters.get(char_id)

    def get_character_name(self, char_id: int, lang: discord.Locale) -> str | None:
        character = self._characters.get(char_id)
        return self.get_loc(character.name_hash, lang) if character else None

    def get_character_full_name(self, char_id: int, lang: discord.Locale) -> str | None:
        character = self._characters.get(char_id)
        return self.get_loc(character.full_name_hash, lang) if character else None

    @property
    def light_cones(self) -> dict[int, HSRLightCone]:
        return self._light_cones

    def get_light_cone(self, lc_id: int) -> HSRLightCone | None:
        return self._light_cones.get(lc_id)

    def get_light_cone_name(self, lc_id: int, lang: discord.Locale) -> str | None:
        light_cone = self._light_cones.get(lc_id)
        return self.get_loc(light_cone.name_hash, lang) if light_cone else None

    @property
    def relics(self) -> dict[int, HSRRelicPiece]:
        return self._relics

    def get_relic(self, relic_id: int) -> HSRRelicPiece | None:
        return self._relics.get(relic_id)

    def get_main_affix(self, group: int, tier: int) -> RelicAffixValue | None:
        data = self._raw["affixes.json"]["MainAffix"].get(str(group), {}).get(str(tier))
        return RelicAffixValue.from_raw(data) if data else None

    def get_sub_affix(self, group: int, tier: int) -> RelicAffixValue | None:
        data = self._raw["affixes.json"]["SubAffix"].get(str(group), {}).get(str(tier))
        return RelicAffixValue.from_raw(data) if data else None

    @property
    def skill_nodes(self) -> dict[int, HSRSkillNode]:
        return self._skill_nodes

    def get_skill_node(self, node_id: int) -> HSRSkillNode | None:
        return self._skill_nodes.get(node_id)

    @property
    def eidolons(self) -> dict[int, HSREidolon]:
        return self._eidolons

    def get_eidolon(self, rank_id: int) -> HSREidolon | None:
        return self._eidolons.get(rank_id)

    @property
    def profile_icons(self) -> dict[int, HSRProfileIcon]:
        return self._profile_icons

    def get_profile_icon(self, icon_id: int) -> HSRProfileIcon | None:
        return self._profile_icons.get(icon_id)
