from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection
from typing import Any, Callable, Generic, TypeVar

from zenox.config import CONFIG

CLUSTER = AsyncMongoClient(CONFIG.db_url)

T = TypeVar("T")


class DBProperty(Generic[T]):
    """Python's @property does not work with type hints, so this is a workaround to make it work."""

    def __init__(self, getter: Callable[[Any], T]) -> None:
        self.getter = getter

    def __get__(self, obj, objtype=None) -> T:
        return self.getter(obj)


class Database:
    def __init__(self):
        self._db = CLUSTER.get_default_database()

    @DBProperty
    def guilds(self) -> AsyncCollection:
        """Collection for guild configurations."""
        return self._db["guilds"]

    @DBProperty
    def videos(self) -> AsyncCollection:
        """Collection for YouTube videos metadata."""
        return self._db["videos"]
    
    @DBProperty
    def codes(self) -> AsyncCollection:
        """Collection for redemption codes."""
        return self._db["codes"]
    
    @DBProperty
    def special_programs(self) -> AsyncCollection:
        """Collection for special programs."""
        return self._db["special_programs"]
    
    @DBProperty
    def config(self) -> AsyncCollection:
        """Collection for global configuration."""
        return self._db["config"]
    
    @DBProperty
    def cache(self) -> AsyncCollection:
        """Collection for caching data."""
        return self._db["cache"]


DB = Database()
