"""Static catalog of Seeleland-tracked light cones per character.

Maps each character to its known (light cone, category-key template) pairs,
so ``/sl3`` can browse leaderboard categories without needing any specific
account's own played data.

Unlike the account-driven path (``SLClient.get_player_data``), each catalog
entry is already the single canonical/featured category for that
(character, light cone) pair - team code and speed-threshold suffix are
often already baked into ``ctgr_template`` as fixed constants (e.g. Jingliu's
``"E0S1_xxxxxPL_134"``), not independently selectable axes.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_LC_PLACEHOLDER = "xxxxx"
_BRACKET_RE = re.compile(r"^(E\d+S\d+)_")


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    light_cone_id: int
    ctgr_template: str

    @property
    def bracket(self) -> str:
        """The E{e}S{s} bracket prefix of this entry's ctgr template."""
        match = _BRACKET_RE.match(self.ctgr_template)
        return match.group(1) if match else ""

    def resolve_ctgr(self) -> str:
        """Resolve this entry's template into a real, ready-to-query ctgr string."""
        return self.ctgr_template.replace(_LC_PLACEHOLDER, str(self.light_cone_id))


# (char_id -> list[(light_cone_id, ctgr_template)]) catalog of tracked builds.
_RAW_CATALOG: dict[int, list[tuple[int, str]]] = {
    1102: [
        (23001, "E0S1_xxxxx"),
        (23001, "E1S1_xxxxx"),
        (23001, "E2S1_xxxxx"),
        (23001, "E2S5_xxxxx"),
        (23046, "E0S1_xxxxx"),
        (23046, "E2S1_xxxxx"),
        (23046, "E2S5_xxxxx"),
        (24001, "E0S5_xxxxx"),
        (23012, "E0S1_xxxxx"),
        (21010, "E0S5_xxxxx"),
    ],
    1212: [
        (23014, "E0S1_xxxxxPL_134"),
        (23009, "E0S1_xxxxxPL_134"),
        (23039, "E0S1_xxxxxPL_134"),
        (21012, "E0S5_xxxxxPL_134"),
        (22003, "E0S5_xxxxxPL_134"),
    ],
    1308: [
        (23024, "E0S1_xxxxx"),
        (23024, "E1S1_xxxxx"),
        (21001, "E0S5_xxxxx"),
        (23004, "E0S1_xxxxx"),
        (21044, "E0S5_xxxxx"),
    ],
    1310: [
        (23025, "E0S1_xxxxxHMC_210"),
        (23025, "E5S1_xxxxxHMC_210"),
        (24000, "E0S5_xxxxxHMC_210"),
        (21042, "E0S5_xxxxxHMC_210"),
        (23002, "E0S1_xxxxxHMC_210"),
        (21038, "E0S5_xxxxxHMC_210"),
    ],
    1220: [
        (23031, "E0S1_xxxxxRB"),
        (23031, "E0S5_xxxxxRB"),
        (24001, "E0S5_xxxxxRB"),
        (23016, "E0S1_xxxxxRB"),
        (23020, "E0S1_xxxxxRB"),
        (23001, "E0S1_xxxxxRB"),
        (23012, "E0S1_xxxxxRB"),
        (21010, "E0S5_xxxxxRB"),
    ],
    1221: [
        (23030, "E0S1_xxxxxRB"),
        (23030, "E6S1_xxxxxRB"),
        (23002, "E0S1_xxxxxRB"),
        (23009, "E0S1_xxxxxRB"),
        (23015, "E0S1_xxxxxRB"),
        (24000, "E0S5_xxxxxRB"),
        (21019, "E0S5_xxxxxRB"),
    ],
    1107: [
        (23002, "E0S1_xxxxxRB"),
        (23030, "E0S1_xxxxxRB"),
        (23009, "E0S1_xxxxxRB"),
        (23015, "E0S1_xxxxxRB"),
        (24000, "E0S5_xxxxxRB"),
        (21019, "E0S5_xxxxxRB"),
        (21012, "E0S5_xxxxxRB"),
    ],
    1204: [
        (23010, "E0S1_xxxxxTY"),
        (21027, "E0S5_xxxxxTY"),
        (21006, "E0S5_xxxxxTY"),
        (21034, "E0S5_xxxxxTY"),
        (21020, "E0S5_xxxxxTY"),
        (23000, "E0S1_xxxxxTY"),
    ],
    1205: [
        (23009, "E0S1_xxxxx"),
        (23009, "E2S1_xxxxx"),
        (23009, "E2S5_xxxxx"),
        (21012, "E0S5_xxxxx"),
        (22003, "E0S5_xxxxx"),
    ],
    1005: [
        (23006, "E0S1_xxxxx_143"),
        (23006, "E1S1_xxxxx_143"),
        (21001, "E0S5_xxxxx_134"),
        (21022, "E0S5_xxxxx_134"),
        (23004, "E0S1_xxxxx_134"),
        (24003, "E0S5_xxxxx_134"),
        (22000, "E0S5_xxxxx_134"),
    ],
    1307: [
        (23022, "E0S1_xxxxx_143"),
        (23022, "E0S5_xxxxx_143"),
        (23047, "E0S1_xxxxx_143"),
        (21008, "E0S5_xxxxx_143"),
        (22000, "E0S5_xxxxx_143"),
        (21041, "E0S5_xxxxx_143"),
        (21001, "E0S5_xxxxx_143"),
    ],
    1112: [
        (23016, "E0S1_xxxxxRB_134"),
        (23016, "E0S5_xxxxxRB_134"),
        (21010, "E0S5_xxxxxRB_134"),
        (24001, "E0S5_xxxxxRB_134"),
        (21037, "E0S5_xxxxxRB_134"),
        (23012, "E0S1_xxxxxRB_134"),
        (21003, "E0S5_xxxxxRB_134"),
    ],
    1302: [
        (23018, "E0S1_xxxxxTY"),
        (23018, "E6S5_xxxxxTY"),
        (21034, "E0S5_xxxxxTY"),
        (21020, "E0S5_xxxxxTY"),
        (21027, "E0S5_xxxxxTY"),
        (21013, "E0S5_xxxxxTY"),
        (23000, "E0S1_xxxxxTY"),
        (23010, "E0S1_xxxxxTY"),
    ],
    1315: [
        (23027, "E0S1_xxxxxRMHMC_143"),
        (23027, "E0S5_xxxxxRMHMC_143"),
        (24001, "E0S5_xxxxxRMHMC_143"),
        (21024, "E0S5_xxxxxRMHMC_143"),
        (20014, "E0S5_xxxxxRMHMC_143"),
        (21010, "E0S5_xxxxxRMHMC_143"),
        (21047, "E0S5_xxxxxRMHMC_143"),
    ],
    1208: [
        (23011, "E0S1_ERRxxxxx_134"),
        (21016, "E0S5_ERRxxxxx_134"),
        (24002, "E0S5_ERRxxxxx_134"),
        (21009, "E0S5_ERRxxxxx_134"),
        (23005, "E0S1_ERRxxxxx_134"),
        (21002, "E0S5_ERRxxxxx_134"),
    ],
    1214: [
        (24000, "E6S5_xxxxxFXHNBRM"),
        (21019, "E6S5_xxxxxFXHNBRM"),
        (21042, "E6S5_xxxxxFXHNBRM"),
        (21005, "E6S5_xxxxxFXHNBRM"),
        (23002, "E6S1_xxxxxFXHNBRM"),
        (23015, "E6S1_xxxxxFXHNBRM"),
    ],
    1003: [
        (23000, "E0S1_xxxxx"),
        (23010, "E0S1_xxxxx"),
        (21027, "E0S5_xxxxx"),
        (21020, "E0S5_xxxxx"),
        (24004, "E0S5_xxxxx"),
        (21034, "E0S5_xxxxx"),
        (21045, "E0S5_xxxxx"),
    ],
    1013: [
        (23000, "E6S1_xxxxxRM"),
        (23010, "E6S1_xxxxxRM"),
        (21020, "E6S5_xxxxxRM"),
        (21006, "E6S5_xxxxxRM"),
        (21027, "E6S5_xxxxxRM"),
        (21013, "E6S5_xxxxxRM"),
        (21034, "E6S5_xxxxxRM"),
        (23018, "E6S1_xxxxxRM"),
        (21040, "E6S5_xxxxxRM"),
    ],
    1103: [
        (23000, "E6S1_xxxxx"),
        (23010, "E6S1_xxxxx"),
        (21020, "E6S5_xxxxx"),
        (21027, "E6S5_xxxxx"),
        (21013, "E6S5_xxxxx"),
        (21034, "E6S5_xxxxx"),
        (23018, "E6S1_xxxxx"),
        (21040, "E6S5_xxxxx"),
    ],
    1217: [
        (23017, "E0S1_xxxxx_134"),
        (23017, "E1S1_xxxxx_134"),
        (22001, "E0S5_xxxxx_134"),
        (21000, "E0S5_xxxxx_134"),
        (23013, "E0S1_xxxxx_134"),
        (21007, "E0S5_xxxxx_134"),
        (21021, "E0S5_xxxxx_134"),
    ],
    1305: [
        (23020, "E0S1_xxxxx"),
        (23020, "E1S1_xxxxx"),
        (24001, "E0S5_xxxxx"),
        (23012, "E0S1_xxxxx"),
        (21003, "E0S5_xxxxx"),
        (21010, "E0S5_xxxxx"),
    ],
    1008: [
        (23009, "E6S1_xxxxx"),
        (23009, "E6S5_xxxxx"),
        (21012, "E6S5_xxxxx"),
        (24000, "E6S5_xxxxx"),
        (21019, "E6S5_xxxxx"),
    ],
    1209: [
        (23012, "E0S1_xxxxxTYPL"),
        (21024, "E0S5_xxxxxTYPL"),
        (24001, "E0S5_xxxxxTYPL"),
        (21010, "E0S5_xxxxxTYPL"),
        (23001, "E0S1_xxxxxTYPL"),
        (23020, "E0S1_xxxxxTYPL"),
    ],
    1213: [
        (23015, "E0S1_xxxxxHNB"),
        (23015, "E0S5_xxxxxHNB"),
        (24000, "E0S5_xxxxxHNB"),
        (21019, "E0S5_xxxxxHNB"),
        (23002, "E0S1_xxxxxHNB"),
    ],
    1201: [
        (21034, "E6S5_xxxxxHNB"),
        (23010, "E6S1_xxxxxHNB"),
        (21027, "E6S5_xxxxxHNB"),
        (21020, "E6S5_xxxxxHNB"),
        (21040, "E6S5_xxxxxHNB"),
        (23000, "E6S1_xxxxxHNB"),
        (23018, "E6S1_xxxxxHNB"),
    ],
    1006: [
        (22000, "E0S5_ERRxxxxx"),
        (23007, "E0S1_ERRxxxxx"),
        (21001, "E0S5_ERRxxxxx"),
        (21015, "E0S5_ERRxxxxx"),
        (23043, "E0S1_ERRxxxxx"),
        (23024, "E0S1_ERRxxxxx"),
    ],
    1317: [
        (23033, "E0S1_xxxxxHMC"),
        (23033, "E1S1_xxxxxHMC"),
        (23033, "E2S1_xxxxxHMC"),
        (23033, "E4S1_xxxxxHMC"),
        (21045, "E0S5_xxxxxHMC"),
        (24004, "E0S5_xxxxxHMC"),
        (21013, "E0S5_xxxxxHMC"),
    ],
    1401: [
        (23037, "E0S1_xxxxxRB"),
        (23037, "E4S1_xxxxxRB"),
        (23010, "E0S1_xxxxxRB"),
        (23000, "E0S1_xxxxxRB"),
        (21034, "E0S5_xxxxxRB"),
        (21020, "E0S5_xxxxxRB"),
        (24004, "E0S5_xxxxxRB"),
    ],
    1314: [
        (23028, "E0S1_xxxxx"),
        (23028, "E2S1_xxxxx"),
        (23037, "E0S1_xxxxx"),
        (23010, "E0S1_xxxxx"),
        (23000, "E0S1_xxxxx"),
        (21034, "E0S5_xxxxx"),
        (21020, "E0S5_xxxxx"),
        (24004, "E0S5_xxxxx"),
    ],
    1402: [
        (23036, "E0S1_xxxxxRB"),
        (23036, "E1S1_xxxxxRB"),
        (23036, "E2S1_xxxxxRB"),
        (23036, "E4S1_xxxxxRB"),
        (21052, "E0S5_xxxxxRB"),
        (20022, "E0S5_xxxxxRB"),
        (21051, "E0S5_xxxxxRB"),
    ],
    1404: [
        (23039, "E0S1_xxxxx"),
        (23039, "E1S1_xxxxx"),
        (23039, "E2S1_xxxxx"),
        (23009, "E0S1_xxxxx"),
        (21012, "E0S5_xxxxx"),
        (22003, "E0S5_xxxxx"),
        (21038, "E0S5_xxxxx"),
    ],
    1407: [
        (23040, "E0S1_xxxxxRMC"),
        (21052, "E0S5_xxxxxRMC"),
        (21050, "E0S5_xxxxxRMC"),
    ],
    1224: [
        (24001, "E6S5_xxxxx"),
        (23012, "E6S1_xxxxx"),
        (23016, "E6S1_xxxxx"),
        (23001, "E6S1_xxxxx"),
        (21010, "E6S5_xxxxx"),
        (21003, "E6S5_xxxxx"),
    ],
    1403: [
        (23038, "E0S1_xxxxxAll"),
        (21018, "E0S5_xxxxxAll"),
        (20012, "E0S5_xxxxxAll"),
    ],
    1405: [
        (23041, "E0S1_xxxxx"),
        (22004, "E0S5_xxxxx"),
        (23037, "E0S1_xxxxx"),
        (23000, "E0S1_xxxxx"),
        (24004, "E0S5_xxxxx"),
    ],
    1409: [
        (23042, "E0S1_ERRxxxxx"),
        (24005, "E0S5_ERRxxxxx"),
        (21054, "E0S5_ERRxxxxx"),
    ],
    1406: [
        (23043, "E0S1_xxxxx"),
        (21015, "E0S5_xxxxx"),
        (21061, "E0S5_xxxxx"),
    ],
    1408: [
        (23044, "E0S1_xxxxx"),
        (23002, "E0S1_xxxxx"),
        (24000, "E0S5_xxxxx"),
        (23015, "E0S1_xxxxx"),
    ],
    1014: [
        (23045, "E0S1_xxxxx"),
        (23002, "E0S1_xxxxx"),
        (24000, "E0S5_xxxxx"),
        (21012, "E0S5_xxxxx"),
        (21058, "E0S5_xxxxx"),
    ],
    1015: [
        (23046, "E0S1_xxxxx"),
        (23020, "E0S1_xxxxx"),
        (23016, "E0S1_xxxxx"),
        (24001, "E0S5_crayonxxxxx"),
        (21003, "E0S5_xxxxx"),
        (21062, "E0S5_xxxxx"),
        (23056, "E0S1_xxxxx"),
    ],
    1410: [
        (23047, "E0S1_xxxxx"),
        (23029, "E0S1_xxxxx"),
        (23022, "E0S1_xxxxx"),
        (23006, "E0S1_xxxxx"),
        (21008, "E0S5_xxxxx"),
        (21001, "E0S5_xxxxx"),
    ],
    1413: [
        (23049, "E0S1_xxxxx"),
        (23049, "E2S1_xxxxx"),
        (23040, "E0S1_xxxxx"),
        (23040, "E2S1_xxxxx"),
        (21057, "E0S5_xxxxx"),
        (21052, "E0S5_xxxxx"),
    ],
    1415: [
        (23052, "E0S1_xxxxx"),
        (23052, "E2S1_xxxxx"),
        (24005, "E0S5_xxxxx"),
        (23042, "E0S1_xxxxx"),
        (21050, "E0S5_xxxxx"),
    ],
    8008: [
        (22006, "E6S5_xxxxx"),
        (21050, "E6S5_xxxxx"),
        (24005, "E6S5_xxxxx"),
    ],
    1501: [
        (23053, "E0S1_ERRxxxxx"),
        (23053, "E2S1_ERRxxxxx"),
        (21064, "E0S5_ERRxxxxx"),
        (21065, "E0S5_ERRxxxxx"),
    ],
    1502: [
        (23054, "E0S1_ERRxxxxx"),
        (23054, "E2S1_ERRxxxxx"),
        (21064, "E0S5_ERRxxxxx"),
        (21065, "E0S5_ERRxxxxx"),
        (24006, "E0S5_ERRxxxxx"),
    ],
    1504: [
        (23056, "E0S1_xxxxx"),
        (23056, "E4S1_xxxxx"),
        (23020, "E0S1_xxxxx"),
        (23016, "E0S1_xxxxx"),
        (24001, "E0S1_xxxxx"),
    ],
    1506: [
        (23057, "E0S1_xxxxx"),
        (21065, "E0S5_xxxxx"),
        (21064, "E0S5_xxxxx"),
    ],
    1004: [
        (23004, "E0S1_xxxxx"),
        (23004, "E4S1_xxxxx"),
        (23004, "E6S1_xxxxx"),
        (23024, "E0S1_xxxxx"),
        (23024, "E4S1_xxxxx"),
        (23024, "E6S1_xxxxx"),
        (22000, "E0S5_xxxxx"),
        (23043, "E0S1_xxxxx"),
        (21015, "E0S5_xxxxx"),
    ],
    1505: [
        (23058, "E0S1_xxxxx"),
        (23058, "E2S1_xxxxx"),
        (21064, "E0S5_xxxxx"),
        (22007, "E0S5_xxxxx"),
        (21065, "E0S5_xxxxx"),
    ],
    1507: [
        (23059, "E0S1_xxxxx"),
        (22000, "E0S5_xxxxx"),
        (23043, "E0S1_xxxxx"),
        (21061, "E0S5_xxxxx"),
        (21015, "E0S5_xxxxx"),
    ],
    1510: [
        (23060, "E0S1_xxxxx"),
        (23037, "E0S1_xxxxx"),
        (23000, "E0S1_xxxxx"),
        (21034, "E0S5_xxxxx"),
        (21040, "E0S5_xxxxx"),
        (21027, "E0S5_xxxxx"),
    ],
    1508: [
        (23061, "E0S1_xxxxx"),
        (23041, "E0S1_xxxxx"),
        (23028, "E0S1_xxxxx"),
        (21060, "E0S5_xxxxx"),
        (24004, "E0S5_xxxxx"),
        (21006, "E0S5_xxxxx"),
        (21013, "E0S5_xxxxx"),
        (21034, "E0S5_xxxxx"),
    ],
}

SEELELAND_LEADERBOARDS_CATALOG: dict[str, list[CatalogEntry]] = {
    str(char_id): [
        CatalogEntry(light_cone_id=light_cone_id, ctgr_template=template) for light_cone_id, template in entries
    ]
    for char_id, entries in _RAW_CATALOG.items()
}


def resolve_catalog_ctgr(light_cone_id: int, template: str) -> str:
    """Resolve a catalog ctgr template into a real, ready-to-query ctgr string."""
    return template.replace(_LC_PLACEHOLDER, str(light_cone_id))


def get_catalog_brackets(char_id: str) -> list[str]:
    """Distinct E{e}S{s} brackets available for a character in the catalog (first-seen order)."""
    seen: dict[str, None] = {}
    for entry in SEELELAND_LEADERBOARDS_CATALOG.get(char_id, []):
        seen.setdefault(entry.bracket, None)
    return list(seen)


def get_catalog_entries_for_bracket(char_id: str, bracket: str) -> list[CatalogEntry]:
    """Catalog entries for a character, scoped to a single bracket."""
    return [entry for entry in SEELELAND_LEADERBOARDS_CATALOG.get(char_id, []) if entry.bracket == bracket]
