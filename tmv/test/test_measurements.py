import pytest
from datetime import datetime, date, timedelta
from structure.organization import Team
from structure.measurements import BurndownMeasurement
from structure.measurements import THCMeasurement, THCQuestion
from structure.measurements import OTMeasurement


class TestOvertimeMeasurement:
    TEAM = None

    def test_common_overtime(self):
        # Positive overtime
        measurement = OTMeasurement(
            measurement_date=date.today(),
            team=TestOvertimeMeasurement.TEAM,
            workdays_fix=20,
            workdays_actual=20,
            overtime=timedelta(hours=12, minutes=21),
        )
        assert measurement is not None

    def test_overtime_more_than_24h(self):
        # Positive overtime >24h
        measurement = OTMeasurement(
            measurement_date=date.today(),
            team=TestOvertimeMeasurement.TEAM,
            workdays_fix=20,
            workdays_actual=20,
            overtime=timedelta(hours=32, minutes=21),
        )
        assert measurement is not None

    def test_overtime_more_than_24h_with_day_value(self):
        # Positive overtime >24h with day value in timedelta
        measurement = OTMeasurement(
            measurement_date=date.today(),
            team=TestOvertimeMeasurement.TEAM,
            workdays_fix=20,
            workdays_actual=20,
            overtime=timedelta(days=1, hours=8, minutes=21),
        )
        assert measurement is not None

    def test_overtime_negative(self):
        # Negative overtime
        measurement = OTMeasurement(
            measurement_date=date.today(),
            team=TestOvertimeMeasurement.TEAM,
            workdays_fix=20,
            workdays_actual=20,
            overtime=timedelta(hours=-10, minutes=10),
        )
        assert measurement is not None

    def test_overtime_high_accuracy(self):
        # Overtime with too accurate OT
        measurement = OTMeasurement(
            measurement_date=date.today(),
            team=TestOvertimeMeasurement.TEAM,
            workdays_fix=20,
            workdays_actual=20,
            overtime=timedelta(hours=42, minutes=8, seconds=28, milliseconds=218),
        )
        assert measurement is not None
