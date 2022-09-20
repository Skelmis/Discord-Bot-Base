from datetime import timedelta, datetime
from typing import Any, Dict, Optional, Generic, TypeVar

from bot_base.caches import Entry
from bot_base.caches.abc import Cache
from bot_base.exceptions import NonExistentEntry, ExistingEntry

KT = TypeVar("KT", bound=Any)
VT = TypeVar("VT", bound=Any)


class TimedCache(Cache, Generic[KT, VT]):
    __slots__ = ("cache", "global_ttl", "non_lazy")

    def __init__(
        self,
        *,
        global_ttl: Optional[timedelta] = None,
        lazy_eviction: bool = False,
    ):
        """
        Parameters
        ----------
        global_ttl: Optional[timedelta]
            A default TTL for any added entries.
        lazy_eviction: bool
            Whether this cache should perform lazy eviction or not.

            Defaults to True
        """
        self.cache: Dict[KT, Entry] = {}
        self.non_lazy: bool = not lazy_eviction
        self.global_ttl: Optional[timedelta] = global_ttl

    def __contains__(self, item: Any) -> bool:
        try:
            entry = self.cache[item]
            if entry.expiry_time and entry.expiry_time < datetime.now():
                self.delete_entry(item)
                return False
        except KeyError:
            return False
        else:
            return True

    def __len__(self):
        self.force_clean()
        return len(self.cache.keys())

    def add_entry(
        self,
        key: KT,
        value: VT,
        *,
        ttl: Optional[timedelta] = None,
        override: bool = False,
    ) -> None:
        """
        Add an entry to the cache.

        Parameters
        ----------
        key
            The key to store this under.
        value
            The item you want to store in the cache
        ttl: Optional[timedelta]
            An optional period of time to expire
            this entry after.
        override: bool
            Whether or not to override an existing value

        Raises
        ------
        ExistingEntry
            You are trying to insert a duplicate key

        Notes
        -----
        ttl passed to this method will
        take precendence over the global ttl.
        """
        self._perform_eviction()
        if key in self and not override:
            raise ExistingEntry

        if ttl or self.global_ttl:
            ttl = ttl or self.global_ttl
            self.cache[key] = Entry(value=value, expiry_time=(datetime.now() + ttl))
        else:
            self.cache[key] = Entry(value=value)

    def delete_entry(self, key: KT) -> None:
        """
        Delete a key from the cache

        Parameters
        ----------
        key
            The key to delete
        """
        self._perform_eviction()
        try:
            self.cache.pop(key)
        except KeyError:
            pass

    def get_entry(self, key: KT) -> VT:
        """
        Fetch a value from the cache

        Parameters
        ----------
        key
            The key you wish to
            retrieve a value for

        Returns
        -------
        VT
            The provided value

        Raises
        ------
        NonExistentEntry
            No value exists in the cache
            for the provided key.

        """
        self._perform_eviction()
        if key not in self:
            raise NonExistentEntry

        return self.cache[key].value

    def force_clean(self) -> None:
        """
        Clear out all outdated cache items.
        """
        now = datetime.now()
        self.cache = {
            k: v
            for k, v in self.cache.items()
            if (v.expiry_time and v.expiry_time > now) or not v.expiry_time
        }

    def _perform_eviction(self):
        if self.non_lazy:
            self.force_clean()
