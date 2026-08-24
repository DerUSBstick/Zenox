from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SeelelandResponse:
    account: AccountData
    leaderboard: dict[str, SeelelandLeaderboardData]

@dataclass
class AccountData:
    id: str
    nm: str
    ach: int
    achrank: str = ""
    icn: str = ""
    sig: str = ""

    @classmethod
    def from_raw(cls, data: dict) -> AccountData:
        return cls(
            id=data["id"],
            nm=data["nm"],
            ach=data["ach"],
            achrank=data.get("achrank", ""),
            icn=data.get("icn", ""),
            sig=data.get("sig", ""),
        )

@dataclass
class CritStats:
    """Crit Rate/DMG (and derived Crit Value) for a specific build, parsed from
    the raw ``effstats`` field (a ``ctgr -> [[stat, value], ...]`` map present
    alongside ``lb`` on both ``getPlayer`` and ``getLbData`` entries).

    ``cv`` uses the common community formula ``CR + CD / 2``.
    """

    cr: float
    cd: float

    @property
    def cv(self) -> float:
        return round(self.cr + self.cd / 2, 1)

    @classmethod
    def from_raw(cls, data: list) -> CritStats | None:
        stats = {stat: float(value.split("%")[0]) for stat, value in data}
        if "CR" not in stats or "CD" not in stats:
            return None
        return cls(cr=stats["CR"], cd=stats["CD"])


@dataclass
class SeelelandLeaderboardData:
    sc: int
    rank: str
    percrank: str
    percraw: float
    crit_stats: CritStats | None = None

    @classmethod
    def from_raw(cls, data: dict, crit_stats: CritStats | None = None) -> SeelelandLeaderboardData:
        return cls(
            sc=data["sc"],
            rank=data["rank"],
            percrank=data["percrank"],
            percraw=data["percraw"],
            crit_stats=crit_stats,
        )


@dataclass
class RelicMainStat:
    stat: str
    value: str

    @classmethod
    def from_raw(cls, data: list) -> RelicMainStat:
        return cls(stat=data[0], value=data[1])


@dataclass
class RelicSubStat:
    stat: str
    value: str
    rolls: int

    @classmethod
    def from_raw(cls, data: list) -> RelicSubStat:
        return cls(stat=data[0], value=data[1], rolls=data[2])


@dataclass
class RelicPiece:
    slot: int
    relic_id: int
    set_id: int
    main_stat: RelicMainStat
    sub_stats: list[RelicSubStat]

    @classmethod
    def from_raw(cls, data: dict) -> RelicPiece:
        return cls(
            slot=data["t"],
            relic_id=data["tid"],
            set_id=data["set"],
            main_stat=RelicMainStat.from_raw(data["m"]),
            sub_stats=[RelicSubStat.from_raw(sb) for sb in data.get("sb", [])],
        )


@dataclass
class LightConeInfo:
    id: str
    superimposition: int

    @classmethod
    def from_raw(cls, data: dict) -> LightConeInfo:
        return cls(id=data["id"], superimposition=data["s"])


@dataclass
class LbEntryScore:
    score: int
    rank: str
    percrank: str
    percraw: float | None = None
    crit_stats: CritStats | None = None

    @classmethod
    def from_raw(cls, data: dict, crit_stats: CritStats | None = None) -> LbEntryScore:
        return cls(
            score=data["sc"],
            rank=data["rank"],
            percrank=data["percrank"],
            percraw=data.get("percraw"),
            crit_stats=crit_stats,
        )


@dataclass
class LbDataEntry:
    uid: str
    char_id: str
    eidolon: int
    light_cone: LightConeInfo
    relics: list[RelicPiece]
    leaderboard: dict[str, LbEntryScore]
    player: AccountData

    @classmethod
    def from_raw(cls, data: dict) -> LbDataEntry:
        effstats_map = data.get("effstats", {})
        return cls(
            uid=data["id"],
            char_id=data["k"],
            eidolon=data["e"],
            light_cone=LightConeInfo.from_raw(data["lc"]),
            # Some very old entries store relics in a legacy shape (just an
            # "icn" icon reference, no "t"/"tid"/"set") - skip those instead of
            # crashing the whole page parse over one player's stale build data.
            relics=[RelicPiece.from_raw(r) for r in data.get("r", []) if "t" in r],
            leaderboard={
                ctgr: LbEntryScore.from_raw(
                    score,
                    crit_stats=CritStats.from_raw(effstats_map[ctgr]) if ctgr in effstats_map else None,
                )
                for ctgr, score in data.get("lb", {}).items()
            },
            player=AccountData.from_raw(data["player"]),
        )


@dataclass
class AchievementLbEntry:
    id: str
    nm: str
    ach: int
    achrank: int
    icn: str = ""
    sig: str = ""

    @classmethod
    def from_raw(cls, data: dict) -> AchievementLbEntry:
        return cls(
            id=data["id"],
            nm=data["nm"],
            ach=data["ach"],
            achrank=data["achrank"],
            icn=data.get("icn", ""),
            sig=data.get("sig", ""),
        )


@dataclass
class RankingsResponse:
    char_id: str
    ctgr: str
    page: int
    entries: list[LbDataEntry] = field(default_factory=list)
