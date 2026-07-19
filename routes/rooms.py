from flask import Blueprint, request, jsonify
from app import db
from models import ConferenceRoom, Booking
from datetime import datetime, timedelta

rooms_bp = Blueprint('rooms', __name__)

BUSINESS_HOURS_START = 9
BUSINESS_HOURS_END = 17

@rooms_bp.route('/rooms', methods=['GET'])
def get_rooms():
    rooms = ConferenceRoom.query.all()
    return jsonify({'data': [r.to_dict() for r in rooms], 'error': None, 'status': 200})

@rooms_bp.route('/rooms/<int:room_id>', methods=['GET'])
def get_room(room_id):
    room = ConferenceRoom.query.get(room_id)
    if not room:
        return jsonify({'data': None, 'error': 'Room not found', 'status': 404}), 404
    return jsonify({'data': room.to_dict(), 'error': None, 'status': 200})

@rooms_bp.route('/rooms/<int:room_id>/availability', methods=['GET'])
def get_availability(room_id):
    """
    Returns a room's booked time slots, optionally filtered by date.
    Optional query param: ?date=YYYY-MM-DD
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
    """
    Returns the free time gaps for a room on a given date, i.e. the
    complement of its booked slots within business hours (09:00-17:00).
    Required query param: ?date=YYYY-MM-DD
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
