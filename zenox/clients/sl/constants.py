"""Seeleland-specific constants: leaderboard category key parsing/formatting.

Maps short team/build codes to human-readable names so leaderboard
categories chosen by a player can be displayed nicely instead of as raw
codes. Not every code is mapped; fall back to the raw code when a lookup
misses.
"""
from __future__ import annotations

# Public Seeleland website (distinct from the API base url in config).
SEELELAND_SITE_URL = "https://seeleland.com/"

# How long a cached Seeleland API response stays "fresh" (seconds). Short-lived
# on purpose - just long enough to cover one command's cascading autocomplete
# calls, not a long-term cache (leaderboard data changes over time).
SEELELAND_CACHE_TTL_SECONDS = 60 * 60 * 12

# Short build/team code -> readable display name.
SEELELAND_TEAM_NAMES: dict[str, str] = {
    "MONOQ": "Fu Xuan + Sparkle + Silver Wolf",
    "FTPMONOQ": "Fu Xuan + Sparkle + Silver Wolf (F2P)",
    # individual characters
    "RB": "Robin",
    "SND": "Sunday",
    "FX": "Fu Xuan",
    "TY": "Tingyun",
    "RM": "Ruan Mei",
    "HH": "Huohuo",
    "BS": "Black Swan",
    "HNB": "Sparkle",
    "PL": "Pela",
    "HMC": "Hatblazer (Harmony)",
    "FUG": "Fugue",
    "BRON": "Bronya",
    "RMC": "Memblazer (Remembrance)",
    "HYA": "Hyacine",
    "HERTA": "Herta",
    "ANAXA": "Anaxa",
    "TRIB": "Tribbie",
    "HNYA": "Hanya",
    "KF": "Kafka",
    "CAS": "Castorice",
    "MEM": "Cyrene",
    "CERY": "Cerydra",
    "EVE": "Evernight",
    "DH": "The Dahlia",
    "YAO": "Yao Guang",
    "SPARX": "Sparxie",
    "EMC": "Trailblazer (Elation)",
    "HNBDDD": "Sparkle",
    "DAHL": "The Dahlia",
    "RMCAMP": "Memblazer (Remembrance) + Amphoreus Planar",
    "ASH": "Ashveil",
    "HIMEV": "Himeko Nova (Verdict)",
    "HIMED": "Himeko Nova (Decimation)",
    "ARCH": "Archer",
    # multi-character teams
    "RMHHBS": "Ruan Mei + Huohuo + Black Swan",
    "RBFX": "Robin + Fu Xuan",
    "SNDFX": "Sunday + Fu Xuan",
    "FXTY": "Fu Xuan + Tingyun",
    "FXHNB": "Fu Xuan + Sparkle",
    "HNBTY": "Sparkle + Tingyun",
    "FXHNBTY": "Fu Xuan + Sparkle + Tingyun",
    "FXRM": "Fu Xuan + Ruan Mei",
    "FXHNBRM": "Fu Xuan + Sparkle + Ruan Mei",
    "RMHH": "Ruan Mei + Huohuo",
    "HMCRM": "Hatblazer (Harmony) + Ruan Mei",
    "FUGRM": "Fugue + Ruan Mei",
    "HMCFUG": "Hatblazer (Harmony) + Fugue",
    "RMBRON": "Ruan Mei + Bronya",
    "RMHMC": "Ruan Mei + Hatblazer (Harmony)",
    "RBHNB": "Robin + Sparkle",
    "RBHNBFX": "Robin + Sparkle + Fu Xuan",
    "RBSND": "Robin + Sunday",
    "SNDHYA": "Sunday + Hyacine",
    "HNBDDDSND": "Sparkle + Sunday",
    "HMCRMFUG": "Hatblazer (Harmony) + Ruan Mei + Fugue",
    "TRIBANAXA": "Tribbie + Anaxa",
    "TYHNYA": "Tingyun + Hanya",
    "RMCHYA": "Memblazer (Remembrance) + Hyacine",
    "RMCHYACAS": "Memblazer (Remembrance) + Hyacine + Castorice",
    "MEMRMC": "Cyrene + Memblazer (Remembrance)",
    "MEMCERY": "Cyrene + Cerydra",
    "MEMHYA": "Cyrene + Hyacine",
    "RMCMEMHYA": "Memblazer (Remembrance) + Cyrene + Hyacine",
    "RMCHYAEVE": "Memblazer (Remembrance) + Hyacine + Evernight",
    "MEMEVE": "Cyrene + Evernight",
    "DHFUG": "The Dahlia + Fugue",
    "SPARXHNB": "Sparxie + Sparkle",
    "SPARXEMC": "Sparxie + Trailblazer (Elation)",
    "CERYHNB": "Cerydra + Sparkle",
    "RMCHNBDDD": "Memblazer (Remembrance) + Sparkle",
    "HNBYAO": "Sparkle + Yao Guang",
    "FUGDAHL": "Fugue + The Dahlia",
    "ASHSNDHYA": "Ashveil + Sunday + Hyacine",
    "ASHSND": "Ashveil + Sunday",
    "HIMEVSND": "Himeko Nova (Verdict) + Sunday",
    "HIMEVD": "Himeko Nova (Verdict) + Himeko Nova (Decimation)",
    # relic-set based categories (Tribbie)
    "All": "Any relics",
    "BONE": "Bone Demesne",
    "LUSH": "Lushaka",
    "VON": "Vonwacq",
    "EAGL": "Eagle",
}

# Canonical per-character display order for build/team codes, "" = base
# (no team suffix). Used only to sort category options consistently with
# Seeleland's own site - NOT a validity filter
SEELELAND_CATEGORY_ORDER: dict[str, list[str]] = {
    "1003": ["", "HMCRMFUG"],
    "1005": ["", "RMHHBS"],
    "1014": ["", "RMC", "SND", "RB"],
    "1015": ["", "HNB", "SND", "CERY"],
    "1102": ["", "CERYHNB", "RMCHNBDDD", "RMC", "SND", "HNBDDDSND"],
    "1107": ["RB", "RBHNB", "RBFX", "RBHNBFX"],
    "1112": ["RB", "RBFX", "SND", "SNDFX"],
    "1201": ["", "FX", "HNB", "FXHNB"],
    "1204": ["TY", "FXTY", "HNBTY", "FXHNBTY", "SND"],
    "1205": ["", "HYA", "SND", "SNDHYA"],
    "1212": ["PL", "FX", "RM", "SND"],
    "1213": ["", "HNB", "RM"],
    "1214": ["", "FX", "FXHNB", "FXRM", "FXHNBRM"],
    "1220": ["RB", "RBFX", "RBSND"],
    "1221": ["RB", "RBHNB", "SND"],
    "1224": [""],
    "1302": ["TY", "TYHNYA"],
    "1307": ["", "KF", "RM", "HH"],
    "1308": ["", "FX", "HNB", "FXHNB"],
    "1310": ["HMC", "FUGRM", "FUGDAHL"],
    "1314": ["", "SND"],
    "1315": ["HMC", "RMBRON", "RMHMC", "FUGRM", "DHFUG"],
    "1317": ["HMC", "HMCRM", "FUGRM", "HMCFUG"],
    "1401": ["", "TRIBANAXA", "RB", "RMC", "FX"],
    "1402": ["RB", "FX", "RMC", "SND", "SNDFX", "MEM"],
    "1403": ["All", "BONE", "LUSH", "VON", "EAGL"],
    "1404": ["", "RMC", "SND", "HNB", "MEM", "MEMRMC"],
    "1405": ["", "HERTA", "SND", "RB", "MEM"],
    "1406": ["", "LUSH"],
    "1407": ["RMC", "TRIB", "SND", "MEM", "MEMRMC"],
    "1408": ["", "SND", "MEM", "CERY", "MEMCERY"],
    "1409": ["", "MEM"],
    "1410": ["", "KF", "RM", "MEM"],
    "1413": ["", "RMCHYA", "MEMHYA", "RMCHYACAS", "RMCMEMHYA"],
    "1415": ["", "HYA", "RMC", "RMCAMP", "RMCHYA", "RMCHYAEVE"],
    "8008": ["", "MEM"],
    "1501": ["", "HNBYAO", "HNB", "YAO"],
    "1502": ["", "HNB", "SPARXHNB"],
    "1504": ["", "HNB", "SND"],
    "1506": ["", "SPARX", "EMC", "SPARXEMC"],
    "1004": ["", "HNBDDDSND", "EAGL"],
    "1505": ["", "YAO", "HNBYAO", "EMC"],
    "1507": ["", "ASH", "HYA", "ASHSND", "ASHSNDHYA"],
    "1508": ["", "ARCH", "HNB", "CERY"],
    "1510": ["", "HIMEV", "HIMED", "HIMEVD", "HIMEVSND"],
}


def get_category_order(char_id: str) -> list[str]:
    """Return the canonical team-code display order for a character id.

    Trailblazer characters expose two numeric ids (one per gender/path
    variant), one apart, sharing the same category order (e.g. ``8007`` and
    ``8008`` both being "Trailblazer (Remembrance)"). If ``char_id`` itself
    has no entry, fall back to ``char_id + 1`` when that's a Trailblazer-range
    id (> 8000).
    """
    if char_id in SEELELAND_CATEGORY_ORDER:
        return SEELELAND_CATEGORY_ORDER[char_id]
    if char_id.isdigit():
        higher_id = str(int(char_id) + 1)
        if int(higher_id) > 8000 and higher_id in SEELELAND_CATEGORY_ORDER:
            return SEELELAND_CATEGORY_ORDER[higher_id]
    return []
