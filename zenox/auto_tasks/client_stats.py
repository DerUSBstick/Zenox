import discord
from zenox.bot.bot import Zenox
from zenox.db.mongodb import DB
from datetime import datetime
from zenox.static.embeds import Embed
from zenox.static.utils import send_webhook

class client_stats:
    
    @classmethod
    def __get_embed(self, guild_count: int, user_count) -> Embed:
        desc = f"Guilds: {guild_count}\nUsers: {user_count}"
        embed = Embed(
            locale=discord.Locale.american_english,
            color=0xf189ff,
            title="Client Stats",
            description=desc
        )
        return embed

    @classmethod
    async def execute(self, client: Zenox):
        try:
            member_count = 0
            guild_count = len(client.guilds)

            for guild in client.guilds:
                member_count += guild.member_count
                DB.guilds.update_one({"id": guild.id}, {"$set": {"memberCount": guild.member_count}})

            DB.const.update_one(
                {"_id": "guild_growth"},
                {"$push": {"growth": {"date": datetime.now(), "guilds": guild_count}}},
                upsert=True
            )
            DB.const.update_one(
                {"_id": "guild_user_growth"},
                {"$push": {"growth": {"date": datetime.now(), "users": member_count}}},
                upsert=True
            )
            embed = self.__get_embed(guild_count, member_count)
            await send_webhook(client.log_webhook_url, username="Client Stats Task", embed=embed)
        except Exception as e:
            client.capture_exception(e)