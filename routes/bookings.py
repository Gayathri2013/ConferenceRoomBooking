from flask import Blueprint, request, jsonify
from app import db
from models import Booking, ConferenceRoom, Employee
from utils.conflict import check_overlap
from datetime import datetime

bookings_bp = Blueprint('bookings', __name__)

@bookings_bp.route('/bookings', methods=['GET'])
def get_bookings():
    """List bookings, optionally filtered by room or organizer.

    Route:
        GET /bookings

    Args:
        room_id (int, optional): Query param. Only return bookings for
            this conference room's ID.
        organizer_id (int, optional): Query param. Only return
            bookings organized by this employee's ID.

    Returns:
        flask.Response: JSON body ``{'data': list[dict], 'error': None,
        'status': 200}`` where each dict is a booking (see
        :meth:`models.Booking.to_dict`). HTTP status 200.

    Examples:
        Example 1 - Python requests, all bookings::

            import requests
            resp = requests.get('http://localhost:5000/bookings')
            print(resp.json())

        Example 2 - Python requests, filter by room::

            resp = requests.get(
                'http://localhost:5000/bookings',
                params={'room_id': 1}
            )
            print(resp.json())

        Browser:
            http://localhost:5000/bookings
            http://localhost:5000/bookings?room_id=1&organizer_id=3

        cURL:
            curl -X GET "http://localhost:5000/bookings"
            curl -X GET "http://localhost:5000/bookings?room_id=1"
    """
    room_id = request.args.get('room_id', type=int)
    organizer_id = request.args.get('organizer_id', type=int)
    query = Booking.query
    if room_id:
        query = query.filter_by(room_id=room_id)
    if organizer_id:
        query = query.filter_by(organizer_id=organizer_id)
    bookings = query.all()
    return jsonify({'data': [b.to_dict() for b in bookings], 'error': None, 'status': 200})

@bookings_bp.route('/bookings/<int:booking_id>', methods=['GET'])
def get_booking(booking_id):
    """Fetch a single booking by its ID.

    Route:
        GET /bookings/<booking_id>

    Args:
        booking_id (int): Path parameter. Primary key of the booking
            to retrieve.

    Returns:
        flask.Response: On success, JSON body ``{'data': dict,
        'error': None, 'status': 200}`` with the booking (see
        :meth:`models.Booking.to_dict`), HTTP status 200. If no
        booking with that ID exists, ``{'data': None, 'error':
        'Booking not found', 'status': 404}`` with HTTP status 404.

    Examples:
        Example 1 - Python requests::

            import requests
            resp = requests.get('http://localhost:5000/bookings/1')
            print(resp.json())

        Example 2 - JavaScript fetch::

            fetch('http://localhost:5000/bookings/1')
              .then(res => res.json())
              .then(data => console.log(data));

        Browser:
            http://localhost:5000/bookings/1

        cURL:
            curl -X GET http://localhost:5000/bookings/1
    """
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'data': None, 'error': 'Booking not found', 'status': 404}), 404
    return jsonify({'data': booking.to_dict(), 'error': None, 'status': 200})

@bookings_bp.route('/bookings', methods=['POST'])
def create_booking():
    """Create a new booking for a conference room.

    Route:
        POST /bookings

    Args:
        room_id (int): Required. JSON body field. ID of the room to book.
        organizer_id (int): Required. JSON body field. ID of the
            employee organizing the meeting.
        start_time (str): Required. JSON body field. ISO 8601
            datetime string, e.g. ``'2026-07-20T09:00:00'``.
        end_time (str): Required. JSON body field. ISO 8601 datetime
            string, must be after ``start_time``.
        meeting_title (str, optional): JSON body field. Title of the
            meeting. Defaults to ``''``.
        attendees (int, optional): JSON body field. Expected number of
            attendees. Defaults to ``1``.

    Returns:
        flask.Response: On success, JSON body ``{'data': dict,
        'error': None, 'status': 201}`` with the created booking (see
        :meth:`models.Booking.to_dict`), HTTP status 201. Returns 400
        if required fields are missing or the datetime format/order
        is invalid, or 409 if the room is already booked for an
        overlapping time slot.

    Examples:
        Example 1 - Python requests::

            import requests
            resp = requests.post(
                'http://localhost:5000/bookings',
                json={
                    'room_id': 1,
                    'organizer_id': 2,
                    'start_time': '2026-07-20T09:00:00',
                    'end_time': '2026-07-20T09:30:00',
                    'meeting_title': 'Sprint Planning',
                    'attendees': 5
                }
            )
            print(resp.status_code, resp.json())

        Example 2 - JavaScript fetch::

            fetch('http://localhost:5000/bookings', {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({
                room_id: 1,
                organizer_id: 2,
                start_time: '2026-07-20T09:00:00',
                end_time: '2026-07-20T09:30:00'
              })
            }).then(res => res.json()).then(console.log);

        Browser:
            Not applicable — browsers cannot issue a POST with a JSON
            body by simply navigating to a URL. Use curl, fetch, or an
            HTML form/JS client instead.

        cURL:
            curl -X POST http://localhost:5000/bookings \\
              -H "Content-Type: application/json" \\
              -d "{\\"room_id\\": 1, \\"organizer_id\\": 2, \\"start_time\\": \\"2026-07-20T09:00:00\\", \\"end_time\\": \\"2026-07-20T09:30:00\\", \\"meeting_title\\": \\"Sprint Planning\\", \\"attendees\\": 5}"
    """
    data = request.get_json()
    if not data:
        return jsonify({'data': None, 'error': 'No data provided', 'status': 400}), 400
    required = ['room_id', 'organizer_id', 'start_time', 'end_time']
    for field in required:
        if field not in data:
            return jsonify({'data': None, 'error': f'Missing field: {field}', 'status': 400}), 400
    try:
        start = datetime.fromisoformat(data['start_time'])
        end = datetime.fromisoformat(data['end_time'])
    except ValueError:
        return jsonify({'data': None, 'error': 'Invalid datetime format. Use ISO 8601.', 'status': 400}), 400
    if end <= start:
        return jsonify({'data': None, 'error': 'end_time must be after start_time', 'status': 400}), 400
    if check_overlap(data['room_id'], start, end):
        return jsonify({'data': None, 'error': 'Time slot conflicts with existing booking', 'status': 409}), 409
    booking = Booking(
        room_id=data['room_id'],
        organizer_id=data['organizer_id'],
        start_time=start,
        end_time=end,
        meeting_title=data.get('meeting_title', ''),
        attendees=data.get('attendees', 1),
        status='scheduled'
    )
    db.session.add(booking)
    db.session.commit()
    return jsonify({'data': booking.to_dict(), 'error': None, 'status': 201}), 201

@bookings_bp.route('/bookings/<int:booking_id>', methods=['PUT'])
def reschedule_booking(booking_id):
    """Reschedule an existing booking to a new time slot.

    Route:
        PUT /bookings/<booking_id>

    Args:
        booking_id (int): Path parameter. ID of the booking to reschedule.
        start_time (str): Required. JSON body field. New ISO 8601
            start datetime, e.g. ``'2026-07-20T10:00:00'``.
        end_time (str): Required. JSON body field. New ISO 8601 end
            datetime, must be after ``start_time``.

    Returns:
        flask.Response: On success, JSON body ``{'data': dict,
        'error': None, 'status': 200}`` with the updated booking (see
        :meth:`models.Booking.to_dict`), HTTP status 200. Returns 404
        if the booking doesn't exist, 400 for missing/invalid data,
        or 409 if the new time slot conflicts with another booking in
        the same room.

    Examples:
        Example 1 - Python requests::

            import requests
            resp = requests.put(
                'http://localhost:5000/bookings/1',
                json={
                    'start_time': '2026-07-20T10:00:00',
                    'end_time': '2026-07-20T10:30:00'
                }
            )
            print(resp.json())

        Example 2 - JavaScript fetch::

            fetch('http://localhost:5000/bookings/1', {
              method: 'PUT',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({
                start_time: '2026-07-20T10:00:00',
                end_time: '2026-07-20T10:30:00'
              })
            }).then(res => res.json()).then(console.log);

        Browser:
            Not applicable — browsers cannot issue a PUT request by
            navigating to a URL. Use curl, fetch, or a REST client.

        cURL:
            curl -X PUT http://localhost:5000/bookings/1 \\
              -H "Content-Type: application/json" \\
              -d "{\\"start_time\\": \\"2026-07-20T10:00:00\\", \\"end_time\\": \\"2026-07-20T10:30:00\\"}"
    """
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'data': None, 'error': 'Booking not found', 'status': 404}), 404
    data = request.get_json()
    if not data:
        return jsonify({'data': None, 'error': 'No data provided', 'status': 400}), 400
    try:
        start = datetime.fromisoformat(data['start_time'])
        end = datetime.fromisoformat(data['end_time'])
    except ValueError:
        return jsonify({'data': None, 'error': 'Invalid datetime format. Use ISO 8601.', 'status': 400}), 400
    if end <= start:
        return jsonify({'data': None, 'error': 'end_time must be after start_time', 'status': 400}), 400
    if check_overlap(booking.room_id, start, end, exclude_id=booking_id):
        return jsonify({'data': None, 'error': 'New time slot conflicts with existing booking', 'status': 409}), 409
    booking.start_time = start
    booking.end_time = end
    db.session.commit()
    return jsonify({'data': booking.to_dict(), 'error': None, 'status': 200})

@bookings_bp.route('/bookings/<int:booking_id>', methods=['DELETE'])
def cancel_booking(booking_id):
    """Cancel an existing booking.

    Route:
        DELETE /bookings/<booking_id>

    Note:
        This performs a soft delete: the booking row is kept but its
        ``status`` field is set to ``'cancelled'`` rather than being
        removed from the database.

    Args:
        booking_id (int): Path parameter. ID of the booking to cancel.

    Returns:
        flask.Response: On success, JSON body ``{'data': dict,
        'error': None, 'status': 200}`` with the booking now showing
        ``status: 'cancelled'`` (see :meth:`models.Booking.to_dict`),
        HTTP status 200. Returns 404 if no booking with that ID exists.

    Examples:
        Example 1 - Python requests::

            import requests
            resp = requests.delete('http://localhost:5000/bookings/1')
            print(resp.json())

        Example 2 - JavaScript fetch::

            fetch('http://localhost:5000/bookings/1', { method: 'DELETE' })
              .then(res => res.json())
              .then(data => console.log(data));

        Browser:
            Not applicable — browsers cannot issue a DELETE request by
            navigating to a URL. Use curl, fetch, or a REST client.

        cURL:
            curl -X DELETE http://localhost:5000/bookings/1
    """
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'data': None, 'error': 'Booking not found', 'status': 404}), 404
    booking.status = 'cancelled'
    db.session.commit()
    return jsonify({'data': booking.to_dict(), 'error': None, 'status': 200})
