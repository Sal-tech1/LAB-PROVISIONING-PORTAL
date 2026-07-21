"""
test_garbage_collector.py
Member 4 (SRE) — Week 4 Task 3

PURPOSE:
    Automated tests for garbage_collector.py.
    These run automatically in GitHub Actions every time anyone
    pushes code to the main branch.

WHAT THESE TESTS PROVE:
    1. The 2-hour expiry logic works correctly
    2. Fresh containers are NOT killed
    3. Old containers ARE identified for killing
    4. The age calculation is accurate
    5. Edge cases (exactly at the limit, brand new, very old) work

HOW TO RUN:
    pip install pytest
    pytest tests/test_garbage_collector.py -v

    You should see something like:
    PASSED  test_container_3_hours_is_expired
    PASSED  test_container_30_min_is_not_expired
    ...all green

ABOUT MOCKS:
    We cannot use real Docker containers in tests — that would be slow,
    require Docker to be running, and be unpredictable. Instead we use
    MagicMock to create fake container objects that behave exactly like
    real docker-py containers but are just Python objects in memory.
    This is called "mocking" — standard practice for testing code that
    relies on external services.
"""

import pytest
import sys
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch, call

# ── Import the module we're testing ──────────────────────────────────────────
# We insert the scripts directory into Python's path so we can import from it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from garbage_collector import (
    get_container_age,
    is_expired,
    format_age,
    kill_container,
    MAX_AGE_HOURS,
)


# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def make_container(started_minutes_ago: int, name: str = "test-container") -> MagicMock:
    """
    Creates a fake Docker container object for testing.

    Args:
        started_minutes_ago: How many minutes ago the container "started"
        name: A name for the container (just for readable test output)

    Returns:
        MagicMock that looks and behaves like a real docker-py container

    WHY WE DO THIS:
        Real docker-py containers need a running Docker daemon.
        MagicMock lets us create objects that have the same attributes
        (like .attrs, .short_id, .name) without needing Docker at all.
    """
    start_time = datetime.now(timezone.utc) - timedelta(minutes=started_minutes_ago)

    fake = MagicMock()
    fake.name = name
    fake.short_id = "abc123def456"
    fake.attrs = {
        "State": {
            # Format exactly matches what Docker actually returns
            "StartedAt": start_time.strftime("%Y-%m-%dT%H:%M:%S.%f+00:00"),
            "Status": "running"
        }
    }
    return fake


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: is_expired()
# ══════════════════════════════════════════════════════════════════════════════

class TestIsExpired:
    """
    Tests for the is_expired() function.
    This is the most critical function in the GC — if this is wrong,
    containers either live forever or get killed too early.
    """

    def test_container_3_hours_old_is_expired(self):
        """Container running 3 hours (above 2h limit) should be marked expired."""
        container = make_container(started_minutes_ago=180)
        assert is_expired(container) is True

    def test_container_30_minutes_old_is_not_expired(self):
        """Container running 30 minutes is well within the 2h limit."""
        container = make_container(started_minutes_ago=30)
        assert is_expired(container) is False

    def test_container_exactly_at_limit_is_expired(self):
        """Container at exactly 2h + 1 minute should be expired."""
        container = make_container(started_minutes_ago=121)
        assert is_expired(container) is True

    def test_container_just_under_limit_is_not_expired(self):
        """Container at 1h 59m should NOT be expired yet."""
        container = make_container(started_minutes_ago=119)
        assert is_expired(container) is False

    def test_brand_new_container_is_not_expired(self):
        """A container started 1 minute ago must never be killed."""
        container = make_container(started_minutes_ago=1)
        assert is_expired(container) is False

    def test_very_old_container_is_expired(self):
        """A container running 8 hours is definitely expired."""
        container = make_container(started_minutes_ago=480)
        assert is_expired(container) is True

    def test_custom_max_age_1_hour_catches_90_minute_container(self):
        """With a 1-hour custom limit, a 90-minute container should expire."""
        container = make_container(started_minutes_ago=90)
        assert is_expired(container, max_age_hours=1) is True

    def test_custom_max_age_1_hour_allows_30_minute_container(self):
        """With a 1-hour custom limit, a 30-minute container should be safe."""
        container = make_container(started_minutes_ago=30)
        assert is_expired(container, max_age_hours=1) is False

    def test_custom_max_age_4_hours_allows_3_hour_container(self):
        """With a 4-hour custom limit, a 3-hour container should be safe."""
        container = make_container(started_minutes_ago=180)
        assert is_expired(container, max_age_hours=4) is False

    def test_custom_max_age_4_hours_expires_5_hour_container(self):
        """With a 4-hour custom limit, a 5-hour container should expire."""
        container = make_container(started_minutes_ago=300)
        assert is_expired(container, max_age_hours=4) is True


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: get_container_age()
# ══════════════════════════════════════════════════════════════════════════════

class TestGetContainerAge:
    """Tests for the get_container_age() helper function."""

    def test_returns_timedelta(self):
        """get_container_age() must return a timedelta object."""
        container = make_container(started_minutes_ago=45)
        age = get_container_age(container)
        assert isinstance(age, timedelta)

    def test_age_is_approximately_60_minutes(self):
        """A container started 60 minutes ago should have age ≈ 60 minutes."""
        container = make_container(started_minutes_ago=60)
        age = get_container_age(container)
        # Allow ±2 minute tolerance for test execution time
        assert timedelta(minutes=58) < age < timedelta(minutes=62)

    def test_age_is_approximately_30_minutes(self):
        """A container started 30 minutes ago should have age ≈ 30 minutes."""
        container = make_container(started_minutes_ago=30)
        age = get_container_age(container)
        assert timedelta(minutes=28) < age < timedelta(minutes=32)

    def test_age_is_approximately_2_hours(self):
        """A container started 120 minutes ago should have age ≈ 2 hours."""
        container = make_container(started_minutes_ago=120)
        age = get_container_age(container)
        assert timedelta(minutes=118) < age < timedelta(minutes=122)

    def test_age_is_positive(self):
        """Container age should always be a positive duration."""
        container = make_container(started_minutes_ago=5)
        age = get_container_age(container)
        assert age > timedelta(0)


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: format_age()
# ══════════════════════════════════════════════════════════════════════════════

class TestFormatAge:
    """Tests for the format_age() display helper."""

    def test_formats_2_hours_30_minutes(self):
        """2h 30m should display as '2h 30m'."""
        age = timedelta(hours=2, minutes=30)
        assert format_age(age) == "2h 30m"

    def test_formats_1_hour_exactly(self):
        """Exactly 1 hour should display as '1h 0m'."""
        age = timedelta(hours=1)
        assert format_age(age) == "1h 0m"

    def test_formats_45_minutes(self):
        """45 minutes should display as '0h 45m'."""
        age = timedelta(minutes=45)
        assert format_age(age) == "0h 45m"

    def test_formats_zero(self):
        """Zero duration should display as '0h 0m'."""
        age = timedelta(0)
        assert format_age(age) == "0h 0m"


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: kill_container()
# ══════════════════════════════════════════════════════════════════════════════

class TestKillContainer:
    """
    Tests for kill_container().
    We use patch to mock the docker APIError so we can test
    the failure case without needing a real Docker daemon.
    """

    def test_successful_kill_returns_true(self):
        """When Docker kill succeeds, function should return True."""
        container = make_container(started_minutes_ago=180)
        # container.kill() is already a MagicMock — calling it does nothing
        # and returns a MagicMock (truthy), simulating a successful kill
        result = kill_container(container)
        assert result is True
        container.kill.assert_called_once()  # verify .kill() was actually called

    def test_failed_kill_returns_false(self):
        """When Docker raises an APIError, function should return False (not crash)."""
        import docker.errors
        container = make_container(started_minutes_ago=180)
        # Make .kill() raise an APIError to simulate Docker refusing to kill
        container.kill.side_effect = docker.errors.APIError("Container not found")

        result = kill_container(container)
        assert result is False

    def test_kill_is_called_on_container(self):
        """kill_container() must actually call .kill() on the container object."""
        container = make_container(started_minutes_ago=180)
        kill_container(container)
        container.kill.assert_called_once()


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: Configuration
# ══════════════════════════════════════════════════════════════════════════════

class TestConfiguration:
    """Sanity checks on the module-level configuration."""

    def test_max_age_hours_is_2(self):
        """
        MAX_AGE_HOURS must be 2.
        If you change the limit, update this test too.
        """
        assert MAX_AGE_HOURS == 2

    def test_max_age_hours_is_positive(self):
        """MAX_AGE_HOURS must be greater than zero."""
        assert MAX_AGE_HOURS > 0

    def test_max_age_hours_is_integer(self):
        """MAX_AGE_HOURS must be an integer (not a float like 2.5)."""
        assert isinstance(MAX_AGE_HOURS, int)