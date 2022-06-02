import logging
from collections import namedtuple

from .exceptions import *
from .cancellable_wait_for import CancellableWaitFor
from .bot import BotBase
from .context import BotContext

__version__ = "1.4.8"


logging.getLogger(__name__).addHandler(logging.NullHandler())
VersionInfo = namedtuple("VersionInfo", "major minor micro releaselevel serial")
version_info = VersionInfo(
    major=1,
    minor=4,
    micro=8,
    releaselevel="production",
    serial=0,
)
