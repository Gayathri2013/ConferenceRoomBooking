from models import Booking

def check_overlap(room_id, start_time, end_time, exclude_id=None):
    """
    Check whether a proposed booking slot overlaps with any existing
    scheduled bookings for a given conference room.

    Two bookings overlap when one starts before the other ends AND ends
    after the other starts. This uses strict less-than comparisons so that
    back-to-back bookings (e.g. 09:00-09:30 followed by 09:30-10:00)
    are correctly allowed.

    Args:
        room_id:     ID of the conference room whose schedule to check
        start_time:  Proposed booking start (datetime)
        end_time:    Proposed booking end (datetime)
        exclude_id:  Optional booking ID to ignore (used during rescheduling)

    Returns:
        bool: True if an overlap exists, False if the slot is free.

    Examples:
        Example 1 - checking a new booking before creation::

            from datetime import datetime
            from utils.conflict import check_overlap

            has_conflict = check_overlap(
                room_id=1,
                start_time=datetime(2026, 7, 20, 9, 0),
                end_time=datetime(2026, 7, 20, 9, 30)
            )
            if has_conflict:
                print("Room is already booked for that slot")

        Example 2 - checking a reschedule, excluding the booking itself::

            has_conflict = check_overlap(
                room_id=1,
                start_time=datetime(2026, 7, 20, 10, 0),
                end_time=datetime(2026, 7, 20, 10, 30),
                exclude_id=5
            )

    Note:
        This is an internal helper function, not an HTTP route — it
        has no browser or curl equivalent. It is called by
        :func:`routes.bookings.create_booking` and
        :func:`routes.bookings.reschedule_booking`.
    """
    query = Booking.query.filter(
        Booking.room_id == room_id,
        Booking.status == 'scheduled',
        Booking.start_time < end_time,
        Booking.end_time > start_time,
    )
    if exclude_id:
        query = query.filter(Booking.id != exclude_id)
    return query.first() is not None
