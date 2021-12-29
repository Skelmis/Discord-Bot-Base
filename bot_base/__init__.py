import logging
from collections import namedtuple

from .bot import BotBase
from .context import BotContext
from .exceptions import *

__version__ = "1.3.5"


logging.getLogger(__name__).addHandler(logging.NullHandler())
VersionInfo = namedtuple("VersionInfo", "major minor micro releaselevel serial")
version_info = VersionInfo(
    major=1, minor=3, micro=5, releaselevel="production", serial=0
)
