import logging
from collections import namedtuple

from .bot import BotBase
from .context import BotContext
from .exceptions import *

__version__ = "1.4.0"


logging.getLogger(__name__).addHandler(logging.NullHandler())
VersionInfo = namedtuple("VersionInfo", "major minor micro releaselevel serial")
version_info = VersionInfo(
    major=1,
    minor=4,
    micro=0,
    releaselevel="production",
    serial=0,
)
