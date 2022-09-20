import pytest

from bot_base.caches import TimedCache


@pytest.fixture
def create_timed_cache() -> TimedCache:
    return TimedCache()
