import pytest  # pylint: disable=unused-import
from datetime import datetime, time, timedelta

from helpers.time import to_timedelta


class TestTimeHelpers:
    def test_GivenTimeDelta_ShouldReturnTimeDelta(self):
        td_values = [
            timedelta(hours=42, minutes=14),
            timedelta(hours=1, minutes=20),
            timedelta(hours=10, minutes=0),
            timedelta(hours=0, minutes=0),
            timedelta(hours=1, minutes=2, seconds=3),
        ]

        for td in td_values:
            assert to_timedelta(td) == td

    def test_GivenProperlyFormattedString_ShouldReturnCorrectValue(self):
        # Regular times, positive and negative
        assert to_timedelta("14:42") == timedelta(hours=14, minutes=42)
        assert to_timedelta("-5:15") == timedelta(hours=-5, minutes=-15)
        # Hours = 0, with one and two digits, positive and negative
        assert to_timedelta("0:28") == timedelta(minutes=28)
        assert to_timedelta("00:28") == timedelta(minutes=28)
        assert to_timedelta("-0:10") == timedelta(minutes=-10)
        assert to_timedelta("-00:10") == timedelta(minutes=-10)
        # More than 24 hours, positive and negative
        assert to_timedelta("52:15") == timedelta(hours=52, minutes=15)
        assert to_timedelta("-52:15") == timedelta(hours=-52, minutes=-15)

    def test_GivenJunk_ShouldReturnZero(self):
        junk_values = [
            "hi",
            400,
            None,
        ]

        for jv in junk_values:
            assert to_timedelta(jv) == timedelta(0)

    def test_GivenDatetime_ShouldReturnTimeDeltaFromEpoch(self):
        assert to_timedelta(datetime(1900, 1, 1, 15, 10)) == timedelta(
            hours=15 + 24, minutes=10
        )
        assert to_timedelta(datetime(1900, 1, 2, 3, 18)) == timedelta(
            hours=24 + 3 + 24, minutes=18
        )

    def test_GivenTime_ShouldReturnTimeDelta(self):
        assert to_timedelta(time(15, 10)) == timedelta(hours=15, minutes=10)
