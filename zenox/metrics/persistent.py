from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from prometheus_client import Counter, Gauge

if TYPE_CHECKING:
    from pymongo.asynchronous.collection import AsyncCollection

__all__ = ("PersistentCounter", "load_persistent_counters", "flush_persistent_counters")


class _Child:
    __slots__ = ("_owner", "_labels")

    def __init__(self, owner: PersistentCounter, labels: tuple[str, ...]) -> None:
        self._owner = owner
        self._labels = labels

    def inc(self, amount: float = 1) -> None:
        self._owner._inc(self._labels, amount)


class PersistentCounter:
    instances: ClassVar[list[PersistentCounter]] = []

    def __init__(self, name: str, documentation: str, labelnames: list[str]) -> None:
        self.name = name
        self._counter = Counter(name, documentation, labelnames)
        self._lifetime = Gauge(
            name.removesuffix("_total") + "_lifetime",
            f"{documentation} (all-time, persisted across restarts)",
            labelnames,
        )
        self._pending: dict[tuple[str, ...], float] = {}
        PersistentCounter.instances.append(self)

    def labels(self, *label_values: str) -> _Child:
        return _Child(self, tuple(str(v) for v in label_values))

    def touch(self, *label_values: str) -> None:
        """Create the series at 0 so it is exported before the first increment."""
        labels = tuple(str(v) for v in label_values)
        self._counter.labels(*labels)
        self._lifetime.labels(*labels)

    def _inc(self, labels: tuple[str, ...], amount: float) -> None:
        self._counter.labels(*labels).inc(amount)
        self._lifetime.labels(*labels).inc(amount)
        self._pending[labels] = self._pending.get(labels, 0) + amount

    async def load(self, collection: AsyncCollection) -> None:
        async for doc in collection.find({"metric": self.name}):
            self._lifetime.labels(*doc["labels"]).inc(doc["value"])

    async def flush(self, collection: AsyncCollection) -> None:
        pending, self._pending = self._pending, {}
        error: Exception | None = None
        for labels, amount in pending.items():
            try:
                await collection.update_one(
                    {"metric": self.name, "labels": list(labels)},
                    {"$inc": {"value": amount}},
                    upsert=True,
                )
            except Exception as exc:
                self._pending[labels] = self._pending.get(labels, 0) + amount
                error = exc
        if error is not None:
            raise error


async def load_persistent_counters(collection: AsyncCollection) -> None:
    await collection.create_index([("metric", 1), ("labels", 1)], unique=True)
    for counter in PersistentCounter.instances:
        await counter.load(collection)


async def flush_persistent_counters(collection: AsyncCollection) -> None:
    for counter in PersistentCounter.instances:
        await counter.flush(collection)
