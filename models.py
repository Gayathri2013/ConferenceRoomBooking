from app import db
from datetime import datetime

class ConferenceRoom(db.Model):
    __tablename__ = 'conference_rooms'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    bookings = db.relationship('Booking', backref='room', lazy=True)

    def to_dict(self):
        """Serialize this conference room to a JSON-compatible dict.

        Args:
            None

        Returns:
            dict: With keys ``id`` (int), ``name`` (str), ``capacity``
            (int), and ``location`` (str).

        Examples:
            Example 1 - serialize a single room::

                room = ConferenceRoom.query.get(1)
                print(room.to_dict())
                # {'id': 1, 'name': 'Azure Hall', 'capacity': 30, 'location': 'Building A, Floor 3'}

            Example 2 - serialize all rooms for a JSON response::

                rooms = ConferenceRoom.query.all()
                payload = [r.to_dict() for r in rooms]

        Note:
            This is a plain Python/ORM method, not an HTTP route — it
            has no browser or curl equivalent. It is used internally
            by routes such as ``GET /rooms`` (see
            :func:`routes.rooms.get_rooms`).
        """
        return {'id': self.id, 'name': self.name, 'capacity': self.capacity, 'location': self.location}

class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    bookings = db.relationship('Booking', backref='organizer', lazy=True)

    def to_dict(self):
        """Serialize this employee to a JSON-compatible dict.

        Args:
            None

        Returns:
            dict: With keys ``id`` (int), ``name`` (str), ``email``
            (str), and ``department`` (str).

        Examples:
            Example 1 - serialize a single employee::

                emp = Employee.query.get(1)
                print(emp.to_dict())
                # {'id': 1, 'name': 'Alice Thompson', 'email': 'alice.thompson@corp.com', 'department': 'Engineering'}

            Example 2 - serialize all employees for a JSON response::

                employees = Employee.query.all()
                payload = [e.to_dict() for e in employees]

        Note:
            This is a plain Python/ORM method, not an HTTP route — it
            has no browser or curl equivalent.
        """
        return {'id': self.id, 'name': self.name, 'email': self.email, 'department': self.department}

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('conference_rooms.id'), nullable=False)
    organizer_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    meeting_title = db.Column(db.String(200))
    attendees = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='scheduled')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Serialize this booking to a JSON-compatible dict.

        Args:
            None

        Returns:
            dict: With keys ``id`` (int), ``room_id`` (int),
            ``organizer_id`` (int), ``start_time`` (str, ISO 8601),
            ``end_time`` (str, ISO 8601), ``meeting_title`` (str or
            None), ``attendees`` (int), and ``status`` (str, one of
            ``'scheduled'``/``'cancelled'``).

        Examples:
            Example 1 - serialize a single booking::

                booking = Booking.query.get(1)
                print(booking.to_dict())
                # {'id': 1, 'room_id': 1, 'organizer_id': 1,
                #  'start_time': '2025-07-01T09:00:00', 'end_time': '2025-07-01T09:30:00',
                #  'meeting_title': 'Team Sync 1', 'attendees': 5, 'status': 'scheduled'}

            Example 2 - serialize all bookings for a JSON response::

                bookings = Booking.query.all()
                payload = [b.to_dict() for b in bookings]

        Note:
            This is a plain Python/ORM method, not an HTTP route — it
            has no browser or curl equivalent. It is used internally
            by routes such as ``GET /bookings`` (see
            :func:`routes.bookings.get_bookings`).
        """
        return {
            'id': self.id,
            'room_id': self.room_id,
            'organizer_id': self.organizer_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'meeting_title': self.meeting_title,
            'attendees': self.attendees,
            'status': self.status
        }
