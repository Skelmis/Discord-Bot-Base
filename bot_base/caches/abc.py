from datetime import timedelta
from typing import runtime_checkable, Protocol, Any


@runtime_checkable
class Cache(Protocol):
    def add_entry(
        self, key: Any, value: Any, *, ttl: timedelta = None, override: bool = False
    ) -> None:
        """
        Adds an entry to the cache with an optional time to live.

        Parameters
        ----------
        key: Any
            The key to store this value under
        value: Any
            The value for the given key
        ttl: timedelta, optional
            How long this entry should be valid for.
            Defaults to forever
        override: bool, optional
            If True, overrides an entry if it already exists

        Raises
        ------
        ExistingEntry
        """
        raise NotImplementedError

    def delete_entry(self, key: Any) -> None:
        """
        Deletes an entry in the cache.

        Parameters
        ----------
        key: Any
            The entry to delete

        Notes
        -----
        If the entry doesnt exist this won't act
        differently to if it did exist.
        """
        raise NotImplementedError

    def __contains__(self, item: Any) -> bool:
        """
        Returns True if the item exists in the cache.
        """
        raise NotImplementedError

    def force_clean(self) -> None:
        """
        Iterates over the cache, removing outdated entries.

        Implemented since by default the cache only cleans
        on access. I.e its lazy
        """
        raise NotImplementedError

    def get_entry(self, key: Any) -> Any:
        """
        Parameters
        ----------
        key: Any
            The key to get an entry for

        Returns
        -------
        Any
            The value for this if

        Raises
        ------
        NonExistentEntry
            Either the cache doesn't contain
            the key, or the Entry timed out
        """
        raise NotImplementedError
