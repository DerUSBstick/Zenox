import time
import discord
from typing import ClassVar, Literal
from ..bot.bot import Zenox
from ..db.mongodb import MongoDB
from ..db.structures import GuildConfig
from ..static.utils import send_webhook
from ..static.embeds import Embed

class cleanDB:
    _bot: ClassVar[Zenox]
    _start: int
    _end: int
    _results: dict[str, int]

    @classmethod
    def __reset_vars(self):
        self._results = {'skipped': 0, 'restored': 0, 'pending': 0, 'deleted': 0, 'error': 0}

    @classmethod
    def __incr_val(self, val: Literal["skipped", "restored", "pending", "deleted", "error"]):
        self._results[val] += 1

    @classmethod
    def __get_embed(self) -> Embed:
        desc = f"Guilds\n```\n{self._results['skipped']} Skipped\n{self._results['restored']} Restored\n{self._results['pending']} Pending\n{self._results['deleted']} Deleted\n{self._results['error']} Error\n```"
        embed = Embed(
            locale=discord.Locale.american_english,
            color=0xf189ff,
            title="Database CleanUp Results",
            description=desc
        )
        embed.set_footer(text=f"Task Duration: {round(self._end-self._start, 3)}s")
        return embed
    
    @classmethod
    async def execute(self, client: Zenox):
        self._bot = client
        self.__reset_vars()
        self._start = time.time()

        guilds: list[int] = []
        db_guilds: list[int] = []
        for guild in self._bot.guilds:
            guilds.append(guild.id)
        DB_GUILDS = self._bot.db.guilds.find({},{"_id": 0, "id":1})
        for guild in DB_GUILDS:
            try:
                guild = GuildConfig(guild['id'])
                if guild.id in guilds:
                    db_guilds.append(guild.id)
                    if guild.pending_deletion:
                        guild.updatePendingDeletion(False)
                        self.__incr_val('restored')
                        continue
                    self.__incr_val('skipped')
                else:
                    if guild.pending_deletion:
                        guild.remove_guild()
                        self.__incr_val('deleted')
                        continue
                    guild.updatePendingDeletion(True)
                    self.__incr_val('pending')
            except Exception as e:
                self._bot.capture_exception(e)
                self.__incr_val('error')
        
        for guild in guilds:
            if guild not in db_guilds:
                GuildConfig(guild)
        self._end = time.time()
        await send_webhook(self._bot.log_webhook_url, username="cleanDB Task", embed=self.__get_embed())