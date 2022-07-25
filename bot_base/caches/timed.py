from copy import deepcopy
from datetime import timedelta, datetime
from typing import Any, Dict, Optional

from bot_base.caches import Entry
from bot_base.caches.abc import Cache
from bot_base.exceptions import NonExistentEntry, ExistingEntry


# This class is unit-tested in my AntiSpam repo
class TimedCache(Cache):
    __slots__ = ("cache",)

    def __init__(self, *, global_ttl: Optional[timedelta] = None):
        self.global_ttl: Optional[timedelta] = global_ttl
        self.cache: Dict[Any, Entry] = {}

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
        key: Any,
        value: Any,
        *,
        ttl: timedelta = None,
        override: bool = False,
    ) -> None:
        if key in self and not override:
            raise ExistingEntry

        if ttl or self.global_ttl:
            ttl = ttl or self.global_ttl
            self.cache[key] = Entry(value=value, expiry_time=(datetime.now() + ttl))
        else:
            self.cache[key] = Entry(value=value)

    def delete_entry(self, key: Any) -> None:
        try:
            self.cache.pop(key)
        except KeyError:
            pass

    def get_entry(self, key: Any) -> Any:
        if key not in self:
            raise NonExistentEntry

        return self.cache[key].value

    def force_clean(self) -> None:
        now = datetime.now()
        for k, v in deepcopy(self.cache).items():
            if v.expiry_time and v.expiry_time < now:
                self.delete_entry(k)
