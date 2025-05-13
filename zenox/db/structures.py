import discord
import datetime
import json
import os
import argparse
import pytz
import sentry_sdk
from dateutil import parser
from .mongodb import DB, HOYOVERSEDB
from ..static import emojis
from ..static.constants import DatabaseKey, GAME_THUMBNAILS, HOYO_REDEEM_URLS
from ..l10n import LocaleStr
from ..static.embeds import Embed
from ..static.enums import Game
from ..ui.components import View, Button
from typing import TypeVar, Generic, TypedDict, Any, Literal
from bson.codec_options import CodecOptions

class AutoStreamCodesConfig:
    def __init__(self, cfg: dict[str, int | str]):
        self.channel = cfg['channel']
        self.message = cfg['message']
        self.stream_time = cfg["stream_time"]
        self.version = cfg["version"]
        self.disabled = cfg["disabled"]

class Config:
    def __init__(self, args: argparse.Namespace) -> None:
        self.schedule = args.schedule
        cfg = self.load_config_file()
        self.auto_stream_codes_config: dict[Game, AutoStreamCodesConfig] = {
            Game.GENSHIN: AutoStreamCodesConfig(cfg[os.environ['ENV']][DatabaseKey[Game.GENSHIN]]["auto-stream-codes"]),
            Game.STARRAIL: AutoStreamCodesConfig(cfg[os.environ['ENV']][DatabaseKey[Game.STARRAIL]]["auto-stream-codes"]),
            Game.ZZZ: AutoStreamCodesConfig(cfg[os.environ['ENV']][DatabaseKey[Game.ZZZ]]["auto-stream-codes"])
        }
    
    def update_class_config(self, game: Game, new_conf: AutoStreamCodesConfig):
        self.auto_stream_codes_config[game] = new_conf
    
    def update_config_file(self):
        conf = self.load_config_file()
        _env = os.environ['ENV']
        for game in Game:
            for k, v in vars(self.auto_stream_codes_config[game]).items():
                conf[_env][DatabaseKey[game]]["auto-stream-codes"][k] = v
        self.dump_config_file(conf)

    def load_config_file(self):
        with open("./zenox/bot/data/zenox.json") as file:
            cfg = json.load(file)
        return cfg
    
    def dump_config_file(self, cfg):
        with open("./zenox/bot/data/zenox.json", "w+") as file:
            json.dump(cfg, file, indent=4)

class UserSettings:
    def __init__(self, settings: dict[str, str | bool]) -> None:
        self.language: discord.Locale = discord.Locale(settings["language"])
        self.dark_mode: bool = settings["dark_mode"]
        self.dyk: bool = settings["dyk"]

class UserConfig:
    cache = {}

    @classmethod
    def __get_cache(cls, userID: int):
        return cls.cache[userID] if userID in cls.cache else None
    def __new__(cls, userID: int):
        existing = cls.__get_cache(userID)
        if existing:
            return existing
        user = super().__new__(cls)
        return user
    def __init__(self, userID: int) -> None:
        if userID == None:
            pass
        if userID in self.cache:
            return
        gld = DB.users.find_one({"id": userID})

        if not gld: # User doesn't exist yet
            self.addUser(userID=userID)
            gld = DB.users.find_one({"id": userID})
        
        self.id: int = gld["id"]
        self.features: list = gld["features"]
        self.flags: list = gld["flags"]
        self.settings: UserSettings = UserSettings(gld["settings"])

    @classmethod
    def addUser(self, userID: int) -> None:
        features = [] # List of features the user has access to (Used for private testing)
        DB.users.insert_one(
            {
                "id": userID,
                "features": features,
                "flags": [],
                "settings": {
                    "language": "en-US",
                    "dark_mode": True,
                    "dyk": True
                }
            }
        )
    def _update_val(self, key: str, value: any, operator: str = "$set") -> None:
        DB.users.update_one({"id": self.id}, {operator: {key: value}})

    def updateSetting(self, setting: str, val: any) -> None:
        self.settings.__setattr__(setting, val)
        self._update_val(f"settings.{setting}", setting)
    
    def updateSettings(self, settings: UserSettings) -> None:
        self.settings = settings
        self._update_val("settings.language", settings.language.value)
        self._update_val("settings.dark_mode", settings.dark_mode)
        self._update_val("settings.dyk", settings.dyk)

class CodesConfig:
    def __init__(self, config: dict[str, int | bool | None]):
        self.channel = config["channel"]
        self.everyone_ping = config["everyone_ping"]
        self.role_ping = config["role_ping"]
        self.stream_codes = config["stream_codes"]
        self.all_codes = config["all_codes"]

class EventReminderDict(TypedDict):
    streams: bool

class EventReminderConfig:
    def __init__(self, config: dict[str, bool]):
        configDict = {}
        for key, item in config.items():
            configDict[key] = item
        self.config: EventReminderDict = configDict

class partnerData:
    def __init__(self, data: dict[str, str | None]):
        self.inviteUrl = data["inviteUrl"]
        self.guildName = data["guildName"]
        self.guildMemberCount = data["guildMemberCount"]
        self.guildDescription = data["guildDescription"]

class GuildConfig:
    cache = {}

    @classmethod
    def __get_cache(cls, guildID: int):
        return cls.cache[guildID] if guildID in cls.cache else None
    def __new__(cls, guildID: int):
        existing = cls.__get_cache(guildID)
        if existing:
            return existing
        guild = super().__new__(cls)
        return guild
    def __init__(self, guildID: int) -> None:
        if guildID == None:
            pass
        if guildID in self.cache:
            return
        gld = DB.guilds.find_one({"id": guildID})

        if not gld: # Guild doesn't exist yet
            self.addGuild(guildID=guildID)
            gld = DB.guilds.find_one({"id": guildID})
        
        self.id: int = gld["id"]
        self.memberCount: int | None = gld["memberCount"]
        self.features: list = gld["features"]
        self.flags: list = gld["flags"]
        self.language: discord.Locale = discord.Locale(gld["language"])
        self.executed_help: bool = gld["executed_help"]
        self.pending_deletion: bool = gld["pending_deletion"]
        self.codes_config: dict[Game, CodesConfig] = {
            Game.GENSHIN: CodesConfig(gld[DatabaseKey[Game.GENSHIN]]["codes_config"]),
            Game.STARRAIL: CodesConfig(gld[DatabaseKey[Game.STARRAIL]]["codes_config"]),
            Game.ZZZ: CodesConfig(gld[DatabaseKey[Game.ZZZ]]["codes_config"])
        }
        self.event_reminders: dict[Game, EventReminderConfig] = {
            Game.GENSHIN: EventReminderConfig(gld[DatabaseKey[Game.GENSHIN]]["event_reminders"]),
            Game.STARRAIL: EventReminderConfig(gld[DatabaseKey[Game.STARRAIL]]["event_reminders"]),
            Game.ZZZ: EventReminderConfig(gld[DatabaseKey[Game.ZZZ]]["event_reminders"])
        }
        self.partnerData: partnerData = partnerData(gld["partnerData"])

        self.cache[self.id] = self

        
    @classmethod
    def addGuild(self, guildID: int) -> None:
        features = [] # List of features the Guild has access to (Used for private testing)
        with sentry_sdk.start_transaction(name="Creating Guild Entry"):
            DB.guilds.insert_one(
                {
                    "id": guildID,
                    "memberCount": None,
                    "features": features,
                    "flags": [],
                    "language": "en-US",
                    "executed_help": False,
                    "pending_deletion": False,
                    DatabaseKey[Game.GENSHIN]: {
                        "codes_config": {
                            "channel": None,
                            "everyone_ping": False,
                            "role_ping": None,
                            "stream_codes": True,
                            "all_codes": True
                        },
                        "event_reminders": {
                            "streams": False
                        }
                    },
                    DatabaseKey[Game.STARRAIL]: {
                        "codes_config": {
                            "channel": None,
                            "everyone_ping": False,
                            "role_ping": None,
                            "stream_codes": True,
                            "all_codes": True
                        },
                        "event_reminders": {
                            "streams": False
                        }
                    },
                    DatabaseKey[Game.ZZZ]: {
                        "codes_config": {
                            "channel": None,
                            "everyone_ping": False,
                            "role_ping": None,
                            "stream_codes": True,
                            "all_codes": True
                        },
                        "event_reminders": {
                            "streams": False
                        }
                    },
                    "partnerData": {
                        "inviteUrl": None,
                        "guildName": None,
                        "guildMemberCount": None,
                        "guildDescription": None
                    }
                }
            )

    def remove_guild(self) -> None:
        """Remove a Guild"""
        DB.guilds.delete_one({"id": self.id})
        del self.cache[self.id]
    
    def _update_val(self, key: str, value: any, operator: str = "$set") -> None:
        DB.guilds.update_one({"id": self.id}, {operator: {key: value}})
    
    def updateLanguage(self, language: discord.Locale) -> None:
        self.language = language
        self._update_val("language", language.value)
    
    def updatePendingDeletion(self, state: bool):
        self.pending_deletion = state
        self._update_val("pending_deletion", state)
    
    def updateGameConfigValue(self, game: Game, dataType: CodesConfig | EventReminderConfig, key: str, value: Any):
        if dataType == CodesConfig:
            self.codes_config[game].__setattr__(key, value)
            self._update_val(f"{DatabaseKey[game.value]}.codes_config.{key}", value)
        elif dataType == EventReminderConfig:
            self.event_reminders[game].config[key] = value
            self._update_val(f"{DatabaseKey[game.value]}.event_reminders.{key}", value)
        else:
            raise ValueError
    
    def updatePartnerData(self, key: str, value: str | None):
        self.partnerData.__setattr__(key, value)
        self._update_val(f"partnerData.{key}", value)

class CodeReward:
    def __init__(self, reward: str, amount: int):
        self.reward: str = reward
        self.amount: int = amount

class Code:
    cache = {Game.GENSHIN: {}, Game.STARRAIL: {}, Game.ZZZ: {}}

    @classmethod
    def __get_cache(cls, game: Game, code: str):
        return cls.cache[game][code] if code in cls.cache[game] else None
    def __new__(cls, game: Game, code: str):
        existing = cls.__get_cache(game, code)
        if existing:
            return existing
        code = super().__new__(cls)
        return code
    def __init__(self, game: Game, code: str):
        if code in self.cache[game]:
            return
        gld = HOYOVERSEDB.codes.find_one({"game": game.value, "code": code})
        if not gld:
            self.addCode(game, code)
            gld = HOYOVERSEDB.codes.find_one({"game": game.value, "code": code})
        self.game: Game = Game(gld["game"])
        self.code: str = gld["code"]
        self.is_china: bool | None = gld['is_china']
        self.rewards: list[CodeReward] | None = [CodeReward(x["reward"], x["amount"]) for x in gld["rewards"]] if gld["rewards"] else []
        self.discovered_unix: int | None = gld["discovered_unix"]
        self.expire_unix: int | None = gld["expire_unix"]
        self.published: bool = gld["published"]
        self.redeemed = gld["redeemed"] 

        self.cache[game][code] = self

    def _update_val(self, key: str, value: any, operator: str = "$set"):
        HOYOVERSEDB.codes.update_one({"game": self.game.value, "code": self.code}, {operator: {key: value}})
        self.__setattr__(key, value)

    def _add_reward(self, reward: CodeReward):
        self.rewards.append(reward)
        HOYOVERSEDB.codes.update_one({"game": self.game.value, "code": self.code}, {"$addToSet": {"rewards": {"reward": reward.reward, "amount": reward.amount}}})
        # HOYOVERSEDB.codes.update_one({"game": self.game.value, "code": self.code}, {"$push": {"rewards": [{"reward": reward.reward, "amount": reward.amount}]}})

    @classmethod
    def addCode(self, game: Game, code: str):
        HOYOVERSEDB.codes.insert_one({
            "game": game.value,
            "code": code,
            "is_china": None,
            "rewards": [],
            "discovered_unix": None,
            "expire_unix": None,
            "published": False,
            "redeemed": None
        })
        

class EventReminder:
    cache = {Game.GENSHIN: {}, Game.STARRAIL: {}, Game.ZZZ: {}}

    @classmethod
    def __get_cache(cls, game: Game, version: str):
        return cls.cache[game][version] if version in cls.cache[game] else None
    
    def __new__(cls, game: Game, version: str):
        existing = cls.__get_cache(game, version)
        if existing:
            return existing
        obj = super().__new__(cls)
        return obj
    
    def __init__(self, game: Game, version: str):
        if version in self.cache[game]:
            return
        gld = HOYOVERSEDB.event_reminders.find_one({"game": game.value, "version": version})
        if not gld:
            self.addEventReminder(game, version)
            gld = HOYOVERSEDB.event_reminders.find_one({"game": game.value, "version": version})

        self.game: Game = Game(gld["game"])
        self.version: str = gld["version"]
        self.rtype: str = gld["rtype"]
        self.title: str | None = gld["title"] 
        self.start: datetime.datetime | None = gld["start"].replace(tzinfo=pytz.UTC) if gld["start"] != None else None
        self.end: datetime.datetime | None = gld["end"].replace(tzinfo=pytz.UTC) if gld["end"] != None else None
        self.image: str | None = gld["image"]
        self.published: bool = gld["published"]
        self.events: list[tuple[int, int]] = gld["events"] if gld["events"] else [] # Temporarily stores all created events, cleaned after analytics concluded
    
    def _update_val(self, key: str, value: any, operator: str = "$set") -> None:
        self.__setattr__(key, value)
        HOYOVERSEDB.event_reminders.update_one({"game": self.game.value, "version": self.version}, {operator: {key: value}})

    @classmethod
    def addEventReminder(self, game: Game, version: str):
        HOYOVERSEDB.event_reminders.insert_one(
            {
                "game": game.value,
                "version": version,
                "rtype": "update_stream",
                "title": None,
                "start": None,
                "end": None,
                "image": None,
                "published": False,
                "events": []
            }
        )

class SpecialProgram: # Update to only store data
    cache = {Game.GENSHIN: {}, Game.STARRAIL: {}, Game.ZZZ: {}}

    @classmethod
    def __get_cache(cls, game: Game, version: str):
        return cls.cache[game][version] if version in cls.cache[game] else None
    def __new__(cls, game: Game, version: str):
        existing = cls.__get_cache(game, version)
        if existing:
            return existing
        guild = super().__new__(cls)
        return guild
    def __init__(self, game: Game, version: str):
        if version in self.cache[game]:
            return
        gld = HOYOVERSEDB.special_programs.find_one({"game": game.value, "version": version})
        if not gld:
            self.addSpecialProgram(game, version)
            gld = HOYOVERSEDB.special_programs.find_one({"game": game.value, "version": version})
        self.game = game
        self.version = version
        self.found = gld["found"]
        self.published = gld["published"]
        self.image: str | None = gld["image"]
        self.expire_unix: int | None = gld["expire_unix"]
        self.codes: list[Code] = [Code(self.game, x) for x in gld["codes"]] if gld["codes"] else []

        self.cache[game][version] = self
    
    def _update_val(self, key: str, value: any, operator: str = "$set") -> None:
        HOYOVERSEDB.special_programs.update_one({"game": self.game.value, "version": self.version}, {operator: {key: value}})

    # Move to hoyolabCodes UI
    async def buildMessage(self, client: discord.Client, locale: discord.Locale) -> tuple[View, Embed, list[discord.File]]:
        view = View(author=None, locale=locale)
        codes = ""
        if self.codes:
            for code in self.codes:
                DIRECT_LINK_STR = LocaleStr(key="direct_link").translate(locale)
                codes += f"{code.code} | **[{DIRECT_LINK_STR}]({HOYO_REDEEM_URLS[self.game] + code.code})**\n"
                view.add_item(item=Button(label=code.code, url=HOYO_REDEEM_URLS[self.game] + code.code))
        
        embed = Embed(
            locale=locale,
            color=6649080,
            title=LocaleStr(key="special_program_embed.title", version=self.version),
            description=LocaleStr(key="special_program_embed.description", emj1=emojis.ANNOUNCEMENT, emj2=emojis.BLURPLE_LINK)
        )
        embed.set_thumbnail(url="attachment://thumbnail.png")
        embed.add_field(name=emojis.CODES1+emojis.CODES2+emojis.CODES3, value=codes if self.codes else LocaleStr(key="no_codes_found"))
        if self.image:
            embed.set_image(url=self.image)

        attachments = [discord.File("./zenox-assets/assets/genshin-impact/thumbnails/" + GAME_THUMBNAILS[self.game], filename="thumbnail.png")]

        return view, embed, attachments

    def addCode(self, code: Code):
        if self.codes and any(x.code == code.code for x in self.codes): # Prevent Duplicates
            return
        self.codes.append(code)
        self._update_val(key="codes", value=code.code, operator="$push")
    
    def mark(self, typ: Literal["found", "published"]):
        if not self.__getattribute__(typ):
            self.__setattr__(typ, True)
            self._update_val(typ, True)
        
        if typ == "published":
            for code in self.codes:
                code._update_val("published", True)

    def updateImage(self, img: str):
        self.image = img
        self._update_val("image", img)

    @classmethod
    def addSpecialProgram(self, game: Game, version: str):
        HOYOVERSEDB.special_programs.insert_one(
            {
                "game": game.value,
                "version": version,
                "found": False,
                "published": False,
                "image": None,
                "expire_unix": None,
                "codes": []
            }
        )