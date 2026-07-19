# Conference Room Booking System

## Project Overview
A small Flask REST API for booking company conference rooms. It
models three resources — `ConferenceRoom`, `Employee`, and `Booking`
— stored in a SQLite database (`db/bookings.db`). Employees can list
rooms, check a room's booked slots or free (unbooked) time gaps within
business hours, and create, reschedule, or cancel bookings. Every
booking write path (`POST`/`PUT /bookings`) runs through
`utils/conflict.check_overlap()` to guarantee a room is never
double-booked for overlapping times. There is no web UI — this is a
JSON API only, meant to sit behind a frontend or be called directly
(see examples below). Rooms and employees are read-only through the
API; they only exist via `db/seed_data.py`.

**Example workflow (curl):**
```bash
# 1. See what rooms exist
curl http://localhost:5000/rooms

# 2. Check Azure Hall's (room_id=1) free gaps on a given day
curl "http://localhost:5000/rooms/1/available-slots?date=2026-07-20"

# 3. Book a free slot
curl -X POST http://localhost:5000/bookings \
  -H "Content-Type: application/json" \
  -d '{"room_id": 1, "organizer_id": 2, "start_time": "2026-07-20T09:00:00", "end_time": "2026-07-20T09:30:00", "meeting_title": "Sprint Planning"}'

# 4. Reschedule that booking (assume it came back as id 21)
curl -X PUT http://localhost:5000/bookings/21 \
  -H "Content-Type: application/json" \
  -d '{"start_time": "2026-07-20T10:00:00", "end_time": "2026-07-20T10:30:00"}'

# 5. Cancel it
curl -X DELETE http://localhost:5000/bookings/21
```

## Tech Stack
- Language: Python 3.11
- Framework: Flask 3.0
- ORM: Flask-SQLAlchemy 3.1
- Database: SQLite (db/bookings.db)

## Coding Conventions
- Every route returns the same JSON envelope: `{'data': ..., 'error':
  ..., 'status': <code>}`, and the status code is repeated in both the
  JSON body and the actual HTTP response code.
- Datetimes cross the API boundary as ISO 8601 strings
  (`datetime.fromisoformat()` in, `.isoformat()` out). Query-param
  dates use plain `YYYY-MM-DD` (e.g. `?date=2026-07-20`).
- Cancelling a booking is a soft delete — `DELETE /bookings/<id>` sets
  `status='cancelled'` rather than removing the row.
- Models expose a hand-written `to_dict()` for JSON serialization
  instead of a schema/marshalling library.
- Routes are organized per-resource as blueprints under `routes/`
  (`bookings_bp`, `rooms_bp`) and registered in `create_app()`
  (app.py).
- Business hours are hardcoded constants (`BUSINESS_HOURS_START=9`,
  `BUSINESS_HOURS_END=17`) at the top of `routes/rooms.py`.
- All routes and public methods carry Google-style docstrings
  (purpose, typed Args, Returns, two call examples, browser/curl
  examples) — keep new routes/methods consistent with this.
- Naming conventions observed in the codebase:
  - Model classes are singular PascalCase (`ConferenceRoom`,
    `Employee`, `Booking`) mapped to plural snake_case tables via
    `__tablename__` (`conference_rooms`, `employees`, `bookings`).
  - Blueprint variables are named `<resource>_bp` (`bookings_bp`,
    `rooms_bp`), matching their module filename (`routes/bookings.py`,
    `routes/rooms.py`).
  - Route handler functions are named `<verb>_<noun>` using the
    domain verb for the action rather than generic CRUD names —
    `get_rooms`/`get_room` (GET), `create_booking` (POST),
    `reschedule_booking` (PUT), `cancel_booking` (DELETE) — so the
    function name reads as intent, not just HTTP method.
  - Module-level constants are `UPPER_SNAKE_CASE`
    (`BUSINESS_HOURS_START`, `BUSINESS_HOURS_END`); everything else
    (functions, variables) is `snake_case`.

## Do Not Touch
- `db/bookings.db` — the SQLite data file. Modify data through the
  ORM/API, not by hand.
- The `{'data', 'error', 'status'}` response envelope shape — every
  route follows it; don't introduce a differently-shaped response.
- The overlap check in `utils/conflict.py` (`check_overlap`) uses
  strict `<`/`>` comparisons intentionally so back-to-back bookings
  (e.g. 09:00-09:30 then 09:30-10:00) are allowed. Do not change to
  `<=`/`>=`.
- `SECRET_KEY = 'workshop-secret-key'` in app.py is a hardcoded
  placeholder for the workshop — flag it before any real deployment,
  don't just quietly "fix" it as part of an unrelated change.
- `app.run(debug=True)` in app.py's `__main__` block — Werkzoug's
  debug mode enables an interactive in-browser debugger that allows
  arbitrary code execution if the server is ever reachable outside
  localhost. Fine for this workshop; flag it rather than silently
  toggling it off, and never rely on it being on/off without an
  explicit ask.

## Useful Context
- No authentication or authorization exists on any route — anyone can
  create/reschedule/cancel a booking for any `organizer_id`.
- `db.create_all()` runs on every app startup inside `create_app()`.
  There is no migration tool (no Alembic); schema changes require
  manually dropping/recreating tables (see `db/seed_data.py`).
- `db/seed_data.py` is destructive: running it drops all tables and
  reseeds fixed sample data (5 rooms, 10 employees, 20 bookings dated
  from 2025-07-01). Workshop/demo use only — run with
  `python db/seed_data.py`.
- `tests/` currently only contains an empty `__init__.py` — no tests
  exist yet.
- There are no `POST`/`PUT`/`DELETE` routes for rooms or employees —
  only `Booking` is mutable through the API (`routes/bookings.py`).
  Rooms/employees can only be added or changed by editing
  `db/seed_data.py` and re-running it, or via direct ORM/shell access.
- `attendees` on a booking is stored but never validated against the
  room's `capacity` — e.g. `POST /bookings` happily books a 50-person
  meeting into an 8-capacity room. Also, integer query params
  (`?room_id=`, `?organizer_id=`) use Flask's `type=int` conversion,
  which silently returns `None` on non-numeric input instead of
  raising a 400 — a typo'd filter value is quietly ignored rather than
  erroring.
