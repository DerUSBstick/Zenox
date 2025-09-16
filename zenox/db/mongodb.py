import os
from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection
from typing import Any, Callable, Generic, TypeVar

CLUSTER = AsyncMongoClient(os.getenv("DB_URL"))

T = TypeVar("T")


class DBProperty(Generic[T]):
    """Python's @property does not work with type hints, so this is a workaround to make it work."""

    def __init__(self, getter: Callable[[Any], T]) -> None:
        self.getter = getter

    def __get__(self, obj, objtype=None) -> T:
        return self.getter(obj)


class Database:
    def __init__(self):
        self._db = CLUSTER["zenox"]

    @DBProperty
    def guilds(self) -> AsyncCollection:
        return self._db["guilds"]


DB = Database()
