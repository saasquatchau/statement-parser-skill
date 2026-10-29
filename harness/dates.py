"""Gives every transaction a full date, taking missing years from the printed statement period."""
from datetime import date


def _distance(d, period):
    start, end = period
    return 0 if start <= d <= end else min(abs((d - start).days), abs((d - end).days))


def full_date(printed, period):
    """`printed` is a date, or a (day, month) pair when the statement prints no year."""
    if isinstance(printed, date):
        return printed
    day, month = printed
    candidates = {date(year, month, day) for year in (period[0].year, period[1].year)}
    return min(candidates, key=lambda d: _distance(d, period))


# Issuers often list charges made a few days before the period starts; a date further out than this usually means
# a year was inferred wrongly, which is worth a warning.
OUTSIDE_TOLERANCE_DAYS = 31


def outside(d, period):
    return _distance(d, period) > OUTSIDE_TOLERANCE_DAYS
