from __future__ import annotations

import asyncio
import secrets
from typing import TYPE_CHECKING, Optional, Any

if TYPE_CHECKING:
    from bot_base import BotBase


class CancellableWaitFor:
    def __init__(self, bot: BotBase, *, event, check=None, timeout=None):
        self.bot: BotBase = bot

        self._event = event
        self._check = check
        self._timeout = timeout

        self.__is_running: bool = False
        self.__cancel_key = secrets.token_hex(16)

    def copy(self) -> CancellableWaitFor:
        """Creates and returns a new copy of this cancellable event."""
        return CancellableWaitFor(
            self.bot,
            event=self._event,
            check=self._check,
            timeout=self._timeout,
        )

    async def wait(self) -> Optional[Any]:
        """
        Block until your event returns or is cancelled.

        Returns
        -------
        Optional
            This only returns a value if it was not cancelled.
        """
        if self.__is_running:
            raise RuntimeError(
                "Cannot wait on this instance more then once, "
                "possibly meant to wait on a `.copy()` of this instance?"
            )

        self.__is_running = True
        # ?tag multi wait for in discord.gg/dpy
        done, pending = await asyncio.wait(
            [
                self.bot.loop.create_task(
                    self.bot.wait_for(
                        self._event, check=self._check, timeout=self._timeout
                    )
                ),
                self.bot.loop.create_task(self.bot.wait_for(self.__cancel_key)),
            ],
            return_when=asyncio.FIRST_COMPLETED,
        )

        try:
            self.__is_running = False
            result = done.pop().result()
        except Exception as e:
            self.__is_running = False
            # If the first finished task died for any reason,
            # the exception will be replayed here.
            raise e

        for future in done:
            # If any exception happened in any other done tasks
            # we don't care about the exception, but don't want the noise of
            # non-retrieved exceptions
            future.exception()

        for future in pending:
            future.cancel()

        return result

    def cancel(self):
        """Cancel waiting for the event."""
        self.bot.dispatch(self.__cancel_key)
