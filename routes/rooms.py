from flask import Blueprint, request, jsonify
from app import db
from models import ConferenceRoom, Booking
from datetime import datetime, timedelta

rooms_bp = Blueprint('rooms', __name__)

BUSINESS_HOURS_START = 9
BUSINESS_HOURS_END = 17

@rooms_bp.route('/rooms', methods=['GET'])
def get_rooms():
    """List all conference rooms.

    Route:
        GET /rooms

    Args:
        None. Takes no path, query, or body parameters.

    Returns:
        flask.Response: JSON body ``{'data': list[dict], 'error':
        None, 'status': 200}`` where each dict is a room (see
        :meth:`models.ConferenceRoom.to_dict`). HTTP status 200.

    Examples:
        Example 1 - Python requests::

            import requests
            resp = requests.get('http://localhost:5000/rooms')
            print(resp.json())

        Example 2 - JavaScript fetch::

            fetch('http://localhost:5000/rooms')
              .then(res => res.json())
              .then(data => console.log(data));

        Browser:
            http://localhost:5000/rooms

        cURL:
            curl -X GET http://localhost:5000/rooms
    """
    rooms = ConferenceRoom.query.all()
    return jsonify({'data': [r.to_dict() for r in rooms], 'error': None, 'status': 200})

@rooms_bp.route('/rooms/<int:room_id>', methods=['GET'])
def get_room(room_id):
    """Fetch a single conference room by its ID.

    Route:
        GET /rooms/<room_id>

    Args:
        room_id (int): Path parameter. Primary key of the room to
            retrieve.

    Returns:
        flask.Response: On success, JSON body ``{'data': dict,
        'error': None, 'status': 200}`` with the room (see
        :meth:`models.ConferenceRoom.to_dict`), HTTP status 200. If no
        room with that ID exists, ``{'data': None, 'error': 'Room not
        found', 'status': 404}`` with HTTP status 404.

    Examples:
        Example 1 - Python requests::

            import requests
            resp = requests.get('http://localhost:5000/rooms/1')
            print(resp.json())

        Example 2 - JavaScript fetch::

            fetch('http://localhost:5000/rooms/1')
              .then(res => res.json())
              .then(data => console.log(data));

        Browser:
            http://localhost:5000/rooms/1

        cURL:
            curl -X GET http://localhost:5000/rooms/1
    """
    room = ConferenceRoom.query.get(room_id)
    if not room:
        return jsonify({'data': None, 'error': 'Room not found', 'status': 404}), 404
    return jsonify({'data': room.to_dict(), 'error': None, 'status': 200})

@rooms_bp.route('/rooms/<int:room_id>/availability', methods=['GET'])
def get_availability(room_id):
    """Return a room's booked (scheduled) time slots.

    Route:
        GET /rooms/<room_id>/availability

    Args:
        room_id (int): Path parameter. ID of the room to check.
        date (str, optional): Query param. ISO date string
            ``YYYY-MM-DD``. When provided, only bookings starting on
            that calendar date are returned; when omitted, all
            scheduled bookings for the room are returned.

    Returns:
        flask.Response: JSON body ``{'data': list[dict], 'error':
        None, 'status': 200}`` where each dict is a scheduled booking
        (see :meth:`models.Booking.to_dict`), HTTP status 200. Returns
        400 if ``date`` is present but not in ``YYYY-MM-DD`` format.

    Examples:
        Example 1 - Python requests, all scheduled bookings::

            import requests
            resp = requests.get('http://localhost:5000/rooms/1/availability')
            print(resp.json())

        Example 2 - Python requests, filtered by date::

            resp = requests.get(
                'http://localhost:5000/rooms/1/availability',
                params={'date': '2026-07-20'}
            )
            print(resp.json())

        Browser:
            http://localhost:5000/rooms/1/availability
            http://localhost:5000/rooms/1/availability?date=2026-07-20

        cURL:
            curl -X GET "http://localhost:5000/rooms/1/availability?date=2026-07-20"
    """
    date_str = request.args.get('date', type=str)
    query = Booking.query.filter(
        Booking.room_id == room_id,
        Booking.status == 'scheduled'
    )
    if date_str:
        try:
            target_date = datetime.fromisoformat(date_str).date()
            query = query.filter(db.func.date(Booking.start_time) == target_date)
        except ValueError:
            return jsonify({'data': None, 'error': 'Invalid date format. Use YYYY-MM-DD.', 'status': 400}), 400
    bookings = query.all()
    return jsonify({'data': [b.to_dict() for b in bookings], 'error': None, 'status': 200})

@rooms_bp.route('/rooms/<int:room_id>/available-slots', methods=['GET'])
def get_available_slots(room_id):
    """Return the free (unbooked) time gaps for a room on a given date.

    Route:
        GET /rooms/<room_id>/available-slots

    Computes the complement of the room's booked slots within
    business hours (09:00-17:00) for the requested date.

    Args:
        room_id (int): Path parameter. ID of the room to check.
        date (str): Required. Query param. ISO date string
            ``YYYY-MM-DD`` for which to compute free slots.

    Returns:
        flask.Response: On success, JSON body ``{'data': list[dict],
        'error': None, 'status': 200}`` where each dict is a free gap
        of the form ``{'start_time': str, 'end_time': str}`` in ISO
        8601 format, HTTP status 200. Returns 404 if the room doesn't
        exist, or 400 if ``date`` is missing or not in ``YYYY-MM-DD``
        format.

    Examples:
        Example 1 - Python requests::

            import requests
            resp = requests.get(
                'http://localhost:5000/rooms/1/available-slots',
                params={'date': '2026-07-20'}
            )
            print(resp.json())

        Example 2 - JavaScript fetch::

            fetch('http://localhost:5000/rooms/1/available-slots?date=2026-07-20')
              .then(res => res.json())
              .then(data => console.log(data));

        Browser:
            http://localhost:5000/rooms/1/available-slots?date=2026-07-20

        cURL:
            curl -X GET "http://localhost:5000/rooms/1/available-slots?date=2026-07-20"
    """
    room = ConferenceRoom.query.get(room_id)
    if not room:
        return jsonify({'data': None, 'error': 'Room not found', 'status': 404}), 404

    date_str = request.args.get('date', type=str)
    if not date_str:
        return jsonify({'data': None, 'error': 'Missing required query param: date (YYYY-MM-DD)', 'status': 400}), 400
    try:
        target_date = datetime.fromisoformat(date_str).date()
    except ValueError:
        return jsonify({'data': None, 'error': 'Invalid date format. Use YYYY-MM-DD.', 'status': 400}), 400

    day_start = datetime.combine(target_date, datetime.min.time()) + timedelta(hours=BUSINESS_HOURS_START)
    day_end = datetime.combine(target_date, datetime.min.time()) + timedelta(hours=BUSINESS_HOURS_END)

    bookings = Booking.query.filter(
        Booking.room_id == room_id,
        Booking.status == 'scheduled',
        Booking.start_time < day_end,
        Booking.end_time > day_start
    ).order_by(Booking.start_time).all()

    free_slots = []
    cursor = day_start
    for booking in bookings:
        b_start = max(booking.start_time, day_start)
        b_end = min(booking.end_time, day_end)
        if b_start > cursor:
            free_slots.append({'start_time': cursor.isoformat(), 'end_time': b_start.isoformat()})
        if b_end > cursor:
            cursor = b_end
    if cursor < day_end:
        free_slots.append({'start_time': cursor.isoformat(), 'end_time': day_end.isoformat()})

    return jsonify({'data': free_slots, 'error': None, 'status': 200})
