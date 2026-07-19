from datetime import datetime

from app import db as _db
from models import Booking
from utils.conflict import check_overlap


def _make_booking(room_id, start, end, status='scheduled'):
    """Insert a scheduled booking for room_id spanning [start, end)."""
    booking = Booking(
        room_id=room_id,
        organizer_id=1,
        start_time=start,
        end_time=end,
        status=status,
    )
    _db.session.add(booking)
    _db.session.commit()
    return booking


def test_no_overlap(client):
    """A proposed slot with no time intersection is never a conflict."""
    _make_booking(1, datetime(2026, 7, 20, 9, 0), datetime(2026, 7, 20, 9, 30))

    result = check_overlap(1, datetime(2026, 7, 20, 10, 0), datetime(2026, 7, 20, 10, 30))

    assert result is False


def test_exact_overlap(client):
    """A proposed slot identical to an existing booking is a conflict."""
    _make_booking(1, datetime(2026, 7, 20, 9, 0), datetime(2026, 7, 20, 9, 30))

    result = check_overlap(1, datetime(2026, 7, 20, 9, 0), datetime(2026, 7, 20, 9, 30))

    assert result is True


def test_partial_overlap(client):
    """A proposed slot that partially intersects an existing one is a conflict, from either side."""
    _make_booking(1, datetime(2026, 7, 20, 9, 0), datetime(2026, 7, 20, 10, 0))

    starts_inside_ends_after = check_overlap(1, datetime(2026, 7, 20, 9, 30), datetime(2026, 7, 20, 10, 30))
    starts_before_ends_inside = check_overlap(1, datetime(2026, 7, 20, 8, 30), datetime(2026, 7, 20, 9, 30))

    assert starts_inside_ends_after is True
    assert starts_before_ends_inside is True


def test_back_to_back_bookings_are_not_conflicts(client):
    """Adjacent slots that touch but don't overlap (e.g. 09:00-09:30 then 09:30-10:00) are allowed."""
    _make_booking(1, datetime(2026, 7, 20, 9, 0), datetime(2026, 7, 20, 9, 30))

    ends_where_existing_starts = check_overlap(1, datetime(2026, 7, 20, 8, 30), datetime(2026, 7, 20, 9, 0))
    starts_where_existing_ends = check_overlap(1, datetime(2026, 7, 20, 9, 30), datetime(2026, 7, 20, 10, 0))

    assert ends_where_existing_starts is False
    assert starts_where_existing_ends is False


def test_one_booking_fully_contains_another(client):
    """Full containment in either direction (new-inside-existing or existing-inside-new) is a conflict."""
    _make_booking(1, datetime(2026, 7, 20, 9, 0), datetime(2026, 7, 20, 12, 0))

    new_slot_inside_existing = check_overlap(1, datetime(2026, 7, 20, 10, 0), datetime(2026, 7, 20, 10, 30))
    new_slot_contains_existing = check_overlap(1, datetime(2026, 7, 20, 8, 0), datetime(2026, 7, 20, 13, 0))

    assert new_slot_inside_existing is True
    assert new_slot_contains_existing is True
