from datetime import datetime
from typing import Any, Optional

import attr


@attr.s(slots=True)
class Entry:
    value: Any = attr.ib()
    expiry_time: Optional[datetime] = attr.ib(default=None)
