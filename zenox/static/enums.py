from enum import Enum, StrEnum, IntEnum
from typing import Final

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
    ZZZ = "Zenless Zone Zero"

class GenshinCity(StrEnum):
    MONDSTADT = "Mondstadt"
    LIYUE = "Liyue"
    INAZUMA = "Inazuma"
    SUMERU = "Sumeru"
    FONTAINE = "Fontaine"
    NATLAN = "Natlan"