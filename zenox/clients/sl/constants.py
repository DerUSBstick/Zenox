"""Seeleland-specific constants: leaderboard category key parsing/formatting.

Maps short team/build codes to human-readable names so leaderboard
categories chosen by a player can be displayed nicely instead of as raw
codes. Not every code is mapped; fall back to the raw code when a lookup
misses.
"""
from __future__ import annotations

# Public Seeleland website (distinct from the API base url in config).
SEELELAND_SITE_URL = "https://seeleland.com/"

# Time-to-live for cached Seeleland API responses (seconds).
SEELELAND_CACHE_TTL_SECONDS = 60 * 60 * 12

# Short build/team code -> readable display name.
SEELELAND_TEAM_NAMES: dict[str, str] = {
    'MONOQ': 'Fu Xuan + Sparkle + Silver Wolf',
    'FTPMONOQ': 'Fu Xuan + Sparkle + Silver Wolf (F2P)',
    'RB': 'Robin',
    'SND': 'Sunday',
    'FX': 'Fu Xuan',
    'TY': 'Tingyun',
    'RM': 'Ruan Mei',
    'HH': 'Huohuo',
    'BS': 'Black Swan',
    'HNB': 'Sparkle',
    'PL': 'Pela',
    'HMC': 'Hatblazer (Harmony)',
    'FUG': 'Fugue',
    'BRON': 'Bronya',
    'RMC': 'Memblazer (Remembrance)',
    'HYA': 'Hyacine',
    'HERTA': 'Herta',
    'ANAXA': 'Anaxa',
    'TRIB': 'Tribbie',
    'HNYA': 'Hanya',
    'KF': 'Kafka',
    'CAS': 'Castorice',
    'MEM': 'Cyrene',
    'CERY': 'Cerydra',
    'EVE': 'Evernight',
    'DH': 'The Dahlia',
    'YAO': 'Yao Guang',
    'SPARX': 'Sparxie',
    'EMC': 'Trailblazer (Elation)',
    'HNBDDD': 'Sparkle',
    'DAHL': 'The Dahlia',
    'RMCAMP': 'Memblazer (Remembrance) + Amphoreus Planar',
    'ASH': 'Ashveil',
    'HIMEV': 'Himeko Nova (Verdict)',
    'HIMED': 'Himeko Nova (Decimation)',
    'ARCH': 'Archer',
    'SABER': 'Saber',
    'RSPATK': 'Robin • Summeretto (ATK)',
    'RSPCD': 'Robin • Summeretto (CRIT DMG)',
    'RMHHBS': 'Ruan Mei + Huohuo + Black Swan',
    'RBFX': 'Robin + Fu Xuan',
    'SNDFX': 'Sunday + Fu Xuan',
    'FXTY': 'Fu Xuan + Tingyun',
    'FXHNB': 'Fu Xuan + Sparkle',
    'HNBTY': 'Sparkle + Tingyun',
    'FXHNBTY': 'Fu Xuan + Sparkle + Tingyun',
    'FXRM': 'Fu Xuan + Ruan Mei',
    'FXHNBRM': 'Fu Xuan + Sparkle + Ruan Mei',
    'RMHH': 'Ruan Mei + Huohuo',
    'HMCRM': 'Hatblazer (Harmony) + Ruan Mei',
    'FUGRM': 'Fugue + Ruan Mei',
    'HMCFUG': 'Hatblazer (Harmony) + Fugue',
    'RMBRON': 'Ruan Mei + Bronya',
    'RMHMC': 'Ruan Mei + Hatblazer (Harmony)',
    'RBHNB': 'Robin + Sparkle',
    'RBHNBFX': 'Robin + Sparkle + Fu Xuan',
    'RBSND': 'Robin + Sunday',
    'SNDHYA': 'Sunday + Hyacine',
    'HNBDDDSND': 'Sparkle + Sunday',
    'HMCRMFUG': 'Hatblazer (Harmony) + Ruan Mei + Fugue',
    'TRIBANAXA': 'Tribbie + Anaxa',
    'TYHNYA': 'Tingyun + Hanya',
    'RMCHYA': 'Memblazer (Remembrance) + Hyacine',
    'RMCHYACAS': 'Memblazer (Remembrance) + Hyacine + Castorice',
    'MEMRMC': 'Cyrene + Memblazer (Remembrance)',
    'MEMCERY': 'Cyrene + Cerydra',
    'MEMHYA': 'Cyrene + Hyacine',
    'RMCMEMHYA': 'Memblazer (Remembrance) + Cyrene + Hyacine',
    'RMCHYAEVE': 'Memblazer (Remembrance) + Hyacine + Evernight',
    'MEMEVE': 'Cyrene + Evernight',
    'RSPCDHYA': 'Robin • Summeretto (CRIT DMG) + Hyacine',
    'DHFUG': 'The Dahlia + Fugue',
    'SPARXHNB': 'Sparxie + Sparkle',
    'SPARXEMC': 'Sparxie + Trailblazer (Elation)',
    'CERYHNB': 'Cerydra + Sparkle',
    'RMCHNBDDD': 'Memblazer (Remembrance) + Sparkle',
    'HNBYAO': 'Sparkle + Yao Guang',
    'FUGDAHL': 'Fugue + The Dahlia',
    'ASHSNDHYA': 'Ashveil + Sunday + Hyacine',
    'ASHSND': 'Ashveil + Sunday',
    'HIMEVSND': 'Himeko Nova (Verdict) + Sunday',
    'HIMEVHIMED': 'Himeko Nova (Verdict) + Himeko Nova (Decimation)',
    'All': 'Any relics',
    'BONE': 'Bone Demesne',
    'LUSH': 'Lushaka',
    'VON': 'Vonwacq',
    'EAGL': 'Eagle',
}

# Canonical per-character display order for build/team codes, "" = base
# (no team suffix). Used only to sort category options consistently with
# Seeleland's own site - NOT a validity filter
SEELELAND_CATEGORY_ORDER: dict[str, list[str]] = {
    '1003': ['', 'HMCRMFUG'],
    '1005': ['', 'RMHHBS'],
    '1006': [],
    '1008': [],
    '1013': [],
    '1014': ['', 'RMC', 'SND', 'RB'],
    '1015': ['', 'HNB', 'SND', 'CERY'],
    '1102': ['', 'CERYHNB', 'RMCHNBDDD', 'RMC', 'SND', 'HNBDDDSND'],
    '1103': [],
    '1107': ['RB', 'RBHNB', 'RBFX', 'RBHNBFX'],
    '1112': ['RB', 'RBFX', 'SND', 'SNDFX'],
    '1201': ['', 'FX', 'HNB', 'FXHNB'],
    '1204': ['TY', 'FXTY', 'HNBTY', 'FXHNBTY', 'SND'],
    '1205': ['', 'HYA', 'SND', 'SNDHYA'],
    '1208': [],
    '1209': [],
    '1212': ['PL', 'FX', 'RM', 'SND'],
    '1213': ['', 'HNB', 'RM'],
    '1214': ['', 'FX', 'FXHNB', 'FXRM', 'FXHNBRM'],
    '1217': [],
    '1220': ['RB', 'RBFX', 'RBSND'],
    '1221': ['RB', 'RBHNB', 'SND'],
    '1224': [''],
    '1302': ['TY', 'TYHNYA'],
    '1305': [],
    '1307': ['', 'KF', 'RM', 'HH'],
    '1308': ['', 'FX', 'HNB', 'FXHNB'],
    '1310': ['HMC', 'FUGRM', 'FUGDAHL'],
    '1314': ['', 'SND'],
    '1315': ['HMC', 'RMBRON', 'RMHMC', 'FUGRM', 'DHFUG'],
    '1317': ['HMC', 'HMCRM', 'FUGRM', 'HMCFUG'],
    '1401': ['', 'TRIBANAXA', 'RB', 'RMC', 'FX'],
    '1402': ['RB', 'FX', 'RMC', 'SND', 'SNDFX', 'MEM', 'RSPATK'],
    '1403': ['All', 'BONE', 'LUSH', 'VON', 'EAGL'],
    '1404': ['', 'RMC', 'SND', 'HNB', 'MEM', 'MEMRMC'],
    '1405': ['', 'HERTA', 'SND', 'RB', 'MEM'],
    '1406': ['', 'LUSH'],
    '1407': ['RMC', 'TRIB', 'SND', 'MEM', 'MEMRMC'],
    '1408': ['', 'SND', 'MEM', 'CERY', 'MEMCERY'],
    '1409': ['', 'MEM'],
    '1410': ['', 'KF', 'RM', 'MEM'],
    '1413': ['', 'RMCHYA', 'MEMHYA', 'RMCHYACAS', 'RMCMEMHYA', 'RSPCDHYA'],
    '1415': ['', 'HYA', 'RMC', 'RMCAMP', 'RMCHYA', 'RMCHYAEVE'],
    '8008': ['', 'MEM'],
    '1501': ['', 'HNBYAO', 'HNB', 'YAO'],
    '1502': ['', 'HNB', 'SPARXHNB'],
    '1504': ['', 'HNB', 'SND'],
    '1506': ['', 'SPARX', 'EMC', 'SPARXEMC'],
    '1004': ['', 'HNBDDDSND', 'EAGL'],
    '1505': ['', 'YAO', 'HNBYAO', 'EMC'],
    '1507': ['', 'ASH', 'HYA', 'ASHSND', 'ASHSNDHYA'],
    '1508': ['', 'ARCH', 'HNB', 'CERY'],
    '1510': ['', 'HIMEV', 'HIMED', 'HIMEVHIMED', 'HIMEVSND'],
    '1509': ['', 'SABER'],
    '1513': ['', 'YAO', 'ASH'],
    '1512': [''],
    '1503': [''],
    '8007': ['', 'MEM'],
}

def get_speed_breakpoints(char_id: str, ctgr: str) -> list[str]:
    """Speed suffixes for a leaderboard; 'Base' means no suffix. Callers add '999' (AV)."""
    if char_id == '1005':
        if ('E1S1_23006' in ctgr or 'E0S1_23006' in ctgr) and 'RMHHBS' in ctgr:
            return ['Base', '161', '164', '172', '201']
        return ['Base', '134', '143', '161', '164', '172', '201']
    if char_id == '1307':
        return ['Base', '134', '143', '161', '164', '172']
    if char_id == '1102':
        if 'E0' in ctgr or 'E1' in ctgr:
            return ['Base', '161', '172', '201']
        else:
            return ['Base', '201']
    if char_id == '1217':
        return ['Base', '121', '134', '143', '161', '172', '201']
    if char_id == '1112':
        if 'ASTA' in ctgr:
            return ['Base', '172', '201']
        return ['Base', '121', '134', '143', '161', '172', '201']
    if char_id == '1302':
        if 'HNYA' in ctgr:
            return ['Base', '161', '172', '201']
        return ['Base', '121', '134', '143', '161', '172', '201']
    if char_id == '1209':
        if '21024' in ctgr:
            return ['Base', '143', '161', '172']
        return ['Base', '124', '134', '143', '161', '172']
    if char_id == '1310':
        if 'E5S1_23025' in ctgr:
            return ['Base', '210', '228']
        else:
            return ['Base', '210', '225', '226']
    if char_id == '1013':
        return ['Base', '121', '134', '143']
    if char_id == '1204':
        return ['Base', '121', '125', '129', '134', '141']
    if char_id == '1205':
        return ['Base', '121', '134', '143']
    if char_id == '1008':
        return ['Base', '121', '134', '143']
    if char_id == '1003':
        return ['Base', '121', '134', '143']
    if char_id == '1213':
        return ['Base', '118', '121', '134', '143']
    if char_id == '1208':
        return ['Base', '121', '134', '143', '161', '172', '201']
    if char_id == '1212':
        return ['Base', '121', '134', '143', '161']
    if char_id == '1308':
        return ['Base', '121', '134', '143', '161']
    if char_id == '1315':
        return ['Base', '134', '143', '161', '172', '201']
    if char_id == '1221':
        return ['Base']
    if char_id == '1107':
        return ['Base']
    if char_id == '1220':
        return ['Base', '134', '143', '161']
    if char_id == '1317':
        return ['Base', '121', '134', '143', '161', '172']
    if char_id == '1401':
        return ['Base', '111', '121', '134', '143', '161']
    if char_id == '1314':
        return ['Base', '121', '134']
    if char_id == '1402':
        if '23036' in ctgr:
            return ['Base', '237', '263', '267', '271']
        return ['Base', '226', '253']
    if char_id == '1404':
        return ['Base', '121', '134']
    if char_id == '1407':
        return ['Base']
    if char_id == '1224':
        return ['Base', '134', '143']
    if char_id == '1403':
        return ['Base', '121', '134', '143']
    if char_id == '1405':
        return ['Base', '134', '143', '161']
    if char_id == '1006':
        return ['Base', '134', '143', '161']
    if char_id == '1409':
        return ['Base']
    if char_id == '1406':
        return ['Base']
    if char_id == '1408':
        return ['Base', '136']
    if char_id == '1014':
        return ['Base', '134', '143', '161']
    if char_id == '1015':
        return ['Base', '121', '134', '136']
    if char_id == '1410':
        return ['Base', '134', '143', '161']
    if char_id == '1413':
        return ['Base']
    if char_id == '1415':
        return ['Base', '180', '200']
    if char_id == '8008':
        return ['Base', '161', '172', '201']
    if char_id == '1501':
        return ['Base', '134']
    if char_id == '1502':
        return ['Base', '120']
    if char_id == '1504':
        return ['Base', '134']
    if char_id == '1506':
        return ['Base', '160', '200']
    if char_id == '1004':
        return ['Base', '134']
    if char_id == '1505':
        return ['Base', '134']
    if char_id == '1507':
        if '23043' in ctgr:
            return ['Base', '134', '161', '170']
        else:
            return ['Base', '134', '161']
    if char_id == '1508':
        return ['Base', '134', '143']
    if char_id == '1510':
        return ['Base', '134']
    if char_id == '1509':
        return ['Base']
    if char_id == '1513':
        return ['Base', '141', '161', '172', '201']
    if char_id == '1512':
        return ['Base', '160']
    if char_id == '1503':
        return ['Base', '160', '172']
    return ['Base', '121', '134', '143']


def get_category_order(char_id: str) -> list[str]:
    """Return the canonical team-code display order for a character id, or [] if unknown."""
    return SEELELAND_CATEGORY_ORDER.get(char_id, [])
