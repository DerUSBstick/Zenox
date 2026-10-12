"""Typed data models for Honkai: Star Rail store data."""
from __future__ import annotations

from dataclasses import dataclass, field

from zenox.enums import Element, Path, PointType, RelicSlot

__all__ = (
    "CharacterPromotionStats",
    "HSRCharacter",
    "HSREidolon",
    "HSRLightCone",
    "HSRProfileIcon",
    "HSRRelicPiece",
    "HSRSkillNode",
    "LightConePromotionStats",
    "RelicAffixValue",
    "SkillTreeStructure",
)


@dataclass(frozen=True, slots=True)
class CharacterPromotionStats:
    attack_base: float
    attack_add: float
    defence_base: float
    defence_add: float
    hp_base: float
    hp_add: float
    speed_base: float
    crit_chance: float
    crit_damage: float
    base_aggro: float

    @classmethod
    def from_raw(cls, data: dict) -> CharacterPromotionStats:
        return cls(
            attack_base=data["AttackBase"],
            attack_add=data["AttackAdd"],
            defence_base=data["DefenceBase"],
            defence_add=data["DefenceAdd"],
            hp_base=data["HPBase"],
            hp_add=data["HPAdd"],
            speed_base=data["SpeedBase"],
            crit_chance=data["CriticalChance"],
            crit_damage=data["CriticalDamage"],
            base_aggro=data["BaseAggro"],
        )


@dataclass(frozen=True, slots=True)
class LightConePromotionStats:
    hp_base: float
    hp_add: float
    attack_base: float
    attack_add: float
    defence_base: float
    defence_add: float

    @classmethod
    def from_raw(cls, data: dict) -> LightConePromotionStats:
        return cls(
            hp_base=data["BaseHP"],
            hp_add=data["BaseHPAdd"],
            attack_base=data["BaseAttack"],
            attack_add=data["BaseAttackAdd"],
            defence_base=data["BaseDefence"],
            defence_add=data["BaseDefenceAdd"],
        )


def _flatten_ids(items: list) -> list[int]:
    """Flatten a possibly-nested list of skill ids into a flat list of ints."""
    result: list[int] = []
    for item in items:
        if isinstance(item, list):
            result.extend(_flatten_ids(item))
        else:
            result.append(int(item))
    return result


@dataclass(frozen=True, slots=True)
class SkillTreeStructure:
    """One entry of a character's embedded ``SkillTree`` field."""

    base_skill_ids: list[int]
    minor_trace_groups: list[list[int]]
    summon_skill_ids: list[int]

    @classmethod
    def from_raw(cls, data: dict) -> SkillTreeStructure:
        return cls(
            base_skill_ids=_flatten_ids(data.get("AvatarSkills", [])),
            minor_trace_groups=[_flatten_ids(group) for group in data.get("PropSkills", [])],
            summon_skill_ids=_flatten_ids(data.get("SummonSkills", [])),
        )


@dataclass(frozen=True, slots=True)
class HSRCharacter:
    id: int
    name_hash: str
    full_name_hash: str
    rarity: int
    element: Element
    path: Path
    side_icon: str
    action_icon: str
    cutin_icon: str
    rank_ids: list[int]
    skill_ids: list[int]
    skill_tree: dict[str, SkillTreeStructure]
    promotion: dict[int, CharacterPromotionStats]

    @classmethod
    def from_raw(cls, char_id: int, data: dict) -> HSRCharacter:
        return cls(
            id=char_id,
            name_hash=str(data["AvatarName"]["Hash"]),
            full_name_hash=str(data["AvatarFullName"]["Hash"]),
            rarity=data["Rarity"],
            element=Element(data["Element"]),
            path=Path(data["AvatarBaseType"]),
            side_icon=data.get("AvatarSideIconPath", ""),
            action_icon=data.get("ActionAvatarHeadIconPath", ""),
            cutin_icon=data.get("AvatarCutinFrontImgPath", ""),
            rank_ids=[int(i) for i in data.get("RankIDList", [])],
            skill_ids=[int(i) for i in data.get("SkillList", [])],
            skill_tree={
                key: SkillTreeStructure.from_raw(value)
                for key, value in data.get("SkillTree", {}).items()
            },
            promotion={
                int(level): CharacterPromotionStats.from_raw(stats)
                for level, stats in data.get("Promotion", {}).items()
            },
        )


@dataclass(frozen=True, slots=True)
class HSRLightCone:
    id: int
    name_hash: str
    rarity: int
    path: Path
    icon_path: str
    promotion: dict[int, LightConePromotionStats]

    @classmethod
    def from_raw(cls, lc_id: int, data: dict) -> HSRLightCone:
        return cls(
            id=lc_id,
            name_hash=str(data["EquipmentName"]["Hash"]),
            rarity=data["Rarity"],
            path=Path(data["AvatarBaseType"]),
            icon_path=data.get("ImagePath", ""),
            promotion={
                int(level): LightConePromotionStats.from_raw(stats)
                for level, stats in data.get("Promotion", {}).items()
            },
        )


@dataclass(frozen=True, slots=True)
class HSRRelicPiece:
    id: int
    rarity: int
    slot: RelicSlot
    main_affix_group: int
    sub_affix_group: int
    icon_path: str
    set_id: int

    @classmethod
    def from_raw(cls, relic_id: int, data: dict) -> HSRRelicPiece:
        return cls(
            id=relic_id,
            rarity=data["Rarity"],
            slot=RelicSlot(data["Type"]),
            main_affix_group=data["MainAffixGroup"],
            sub_affix_group=data["SubAffixGroup"],
            icon_path=data.get("Icon", ""),
            set_id=data["SetID"],
        )


@dataclass(frozen=True, slots=True)
class RelicAffixValue:
    property: str
    base_value: float
    level_add: float

    @classmethod
    def from_raw(cls, data: dict) -> RelicAffixValue:
        return cls(
            property=data["Property"],
            base_value=data["BaseValue"],
            level_add=data["LevelAdd"],
        )


@dataclass(frozen=True, slots=True)
class HSRSkillNode:
    id: int
    icon_path: str
    point_type: PointType
    props: dict[str, dict[str, float]] = field(default_factory=dict)
    """Per-level stat bonuses granted by this node (level -> {property: value}),
    sourced from tree.json. Empty for nodes without an associated stat bonus
    (e.g. base skills)."""

    @classmethod
    def from_raw(cls, node_id: int, data: dict, props_data: dict | None) -> HSRSkillNode:
        props: dict[str, dict[str, float]] = {}
        for level, level_data in (props_data or {}).items():
            props[level] = level_data.get("props", {})

        return cls(
            id=node_id,
            icon_path=data.get("IconPath", ""),
            point_type=PointType(data["PointType"]),
            props=props,
        )


@dataclass(frozen=True, slots=True)
class HSREidolon:
    id: int
    icon_path: str
    skill_add_level_list: dict[int, int]

    @classmethod
    def from_raw(cls, eidolon_id: int, data: dict) -> HSREidolon:
        raw_mapping = data.get("SkillAddLevelList", {})
        return cls(
            id=eidolon_id,
            icon_path=data.get("IconPath", ""),
            skill_add_level_list={int(k): v for k, v in raw_mapping.items()},
        )


@dataclass(frozen=True, slots=True)
class HSRProfileIcon:
    id: int
    icon_path: str

    @classmethod
    def from_raw(cls, icon_id: int, data: dict) -> HSRProfileIcon:
        return cls(id=icon_id, icon_path=data.get("Icon", ""))
