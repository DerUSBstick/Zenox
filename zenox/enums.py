from __future__ import annotations

from enum import IntEnum, StrEnum


class PrintColors(StrEnum):
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class Game(StrEnum):
    GENSHIN = "Genshin Impact"
    STARRAIL = "Honkai: Star Rail"
    HONKAI = "Honkai Impact 3rd"
    ZZZ = "Zenless Zone Zero"
    HNA = "Honkai: Nexus Anima"


class Element(StrEnum):
    """Honkai: Star Rail character/light-cone damage element."""

    PHYSICAL = "Physical"
    FIRE = "Fire"
    ICE = "Ice"
    WIND = "Wind"
    THUNDER = "Thunder"
    QUANTUM = "Quantum"
    IMAGINARY = "Imaginary"


class Path(StrEnum):
    """Honkai: Star Rail character/light-cone path (raw AvatarBaseType values)."""

    WARRIOR = "Warrior"
    ROGUE = "Rogue"
    MAGE = "Mage"
    SHAMAN = "Shaman"
    KNIGHT = "Knight"
    PRIEST = "Priest"
    WARLOCK = "Warlock"
    MEMORY = "Memory"
    ELATION = "Elation"


class RelicSlot(StrEnum):
    """Honkai: Star Rail relic/ornament equip slot (raw ``Type`` values).

    HEAD/HAND/BODY/FOOT are "Cavern Relics"; NECK/OBJECT are "Planar Ornaments"
    (player-facing names: Planar Sphere / Link Rope, respectively).
    """

    HEAD = "HEAD"
    HAND = "HAND"
    BODY = "BODY"
    FOOT = "FOOT"
    NECK = "NECK"
    OBJECT = "OBJECT"


class PointType(IntEnum):
    """Honkai: Star Rail skill-tree node kind."""

    MINOR_TRACE = 1
    BASE_SKILL = 2
    MAJOR_TRACE = 3
    SERVANT_SKILL = 4
    ALTERNATE_SKILL = 5
