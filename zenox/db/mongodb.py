import sys, os, datetime
from pymongo import MongoClient, collection
from dotenv import load_dotenv

env = os.getenv("ENV")
print(f"MongoDB Environment is {env}")
CLUSTER = MongoClient(os.getenv(f'MONGODB_{env.upper()}'))

class MongoDB:
    _DB = None

    def __init__(self) -> None:
        if env == "prod":
            self._DB = CLUSTER["zenox"] # DB Name
        else:
            self._DB = CLUSTER[f"zenox_{env}"] # DB Name

    @property
    def guilds(self) -> collection.Collection:
        # Stores config for all guilds
        return self._DB["guilds"]
    @property
    def users(self) -> collection.Collection:
        # Stores config for all users
        return self._DB["users"]

    @property
    def const(self) -> collection.Collection:
        # Stores information about bot growth
        return self._DB["const"]

class HoyoverseDB:
    _DB = None

    def __init__(self):
        if env == "prod":
            self._DB = CLUSTER["hoyoverseDB"]
        else:
            self._DB = CLUSTER[f"hoyoverseDB_{env}"]
    @property
    def event_reminders(self) -> collection.Collection:
        return self._DB["event_reminders"]
    @property
    def special_programs(self) -> collection.Collection:
        return self._DB["special_programs"]
    @property
    def codes(self) -> collection.Collection:
        return self._DB["codes"]

class AnalyticsDB:
    _DB = None

    def __init__(self):
        if env == "prod":
            self._DB = CLUSTER["analytics"]
        else:
            self._DB = CLUSTER[f"analytics_{env}"]

    @property
    def reminders(self) -> collection.Collection:
        return self._DB["reminders"]

    @property
    def wiki_codes(self) -> collection.Collection:
        return self._DB["wiki_codes"]
    
    @property
    def hoyolab_codes(self) -> collection.Collection:
        return self._DB["hoyolab_codes"]

DB = MongoDB()
HOYOVERSEDB = HoyoverseDB()
ANALYTICSDB = AnalyticsDB()