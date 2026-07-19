import pytest

from app import create_app, db as _db
from models import ConferenceRoom, Employee


@pytest.fixture
def client():
    """Flask test client backed by an isolated in-memory SQLite database.

    Spins up a fresh Flask app pointed at ``sqlite:///:memory:``
    (instead of the real ``db/bookings.db``), creates the schema, and
    seeds it with exactly one room and one employee, with no bookings.
    The database is torn down after the test completes, so each test
    that uses this fixture gets a clean, isolated slate.

    Args:
        None. This is a pytest fixture — declare it as a test
        function parameter and pytest injects the return value.

    Returns:
        flask.testing.FlaskClient: A test client for issuing requests
        against the seeded app (e.g. ``client.get('/rooms')``).

    Examples:
        Example 1 - list the seeded room::

            def test_get_rooms(client):
                response = client.get('/rooms')
                assert response.status_code == 200
                assert len(response.get_json()['data']) == 1

        Example 2 - create a booking for the seeded room/employee::

            def test_create_booking(client):
                response = client.post('/bookings', json={
                    'room_id': 1,
                    'organizer_id': 1,
                    'start_time': '2026-07-20T09:00:00',
                    'end_time': '2026-07-20T09:30:00',
                })
                assert response.status_code == 201

    Note:
        This is a pytest fixture, not an HTTP route or a function you
        call directly — it has no browser or curl equivalent. Run it
        via ``pytest`` (e.g. ``pytest tests/``).
    """
    app = create_app(test_config={
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'TESTING': True,
    })

    with app.app_context():
        room = ConferenceRoom(name='Test Room', capacity=10, location='Test Building')
        employee = Employee(name='Test Employee', email='test.employee@example.com', department='Engineering')
        _db.session.add_all([room, employee])
        _db.session.commit()

        with app.test_client() as test_client:
            yield test_client

        _db.session.remove()
        _db.drop_all()
