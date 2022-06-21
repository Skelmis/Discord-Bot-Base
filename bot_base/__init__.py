import logging
from collections import namedtuple

from .exceptions import *
from .cancellable_wait_for import CancellableWaitFor
from .bot import BotBase
from .context import BotContext
from .cog import Cog

__version__ = "1.5.1"


logging.getLogger(__name__).addHandler(logging.NullHandler())
VersionInfo = namedtuple("VersionInfo", "major minor micro releaselevel serial")
version_info = VersionInfo(
    major=1,
    minor=5,
    micro=1,
    releaselevel="production",
    serial=0,
)
