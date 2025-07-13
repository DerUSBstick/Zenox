import discord
from zenox.static.utils import ephemeral
from zenox.db.structures import UserConfig
from zenox.static.enums import Game
from zenox.static.exceptions import NoAccountsFoundError
from zenox.ui.hoyo.stats import StatsView

class StatsCommand:
    def __init__(self, user: discord.User | discord.Member) -> None:
        self._user = user
    
    async def run(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=ephemeral(interaction))
        
        supported_games = (Game.GENSHIN, Game.STARRAIL, Game.ZZZ)
        user = UserConfig(self._user.id)
        accounts = user.get_accounts(supported_games)
        if not accounts:
            raise NoAccountsFoundError(supported_games)
        
        view = StatsView(
            accounts=accounts,
            author=self._user,
            locale=user.settings.language
        )
        await view.start(interaction)
        view.message = await interaction.original_response()

