def test_create_booking_success(client):
    """POST /bookings with valid data creates a booking and returns 201."""
    response = client.post('/bookings', json={
        'room_id': 1,
        'organizer_id': 1,
        'start_time': '2026-07-20T09:00:00',
        'end_time': '2026-07-20T09:30:00',
        'meeting_title': 'Sprint Planning',
        'attendees': 5,
    })

    assert response.status_code == 201
    body = response.get_json()
    assert body['error'] is None
    assert body['status'] == 201
    assert body['data']['room_id'] == 1
    assert body['data']['organizer_id'] == 1
    assert body['data']['meeting_title'] == 'Sprint Planning'
    assert body['data']['status'] == 'scheduled'


def test_create_booking_conflict_returns_409(client):
    """POST /bookings for a time slot that overlaps an existing booking in the same room is rejected."""
    client.post('/bookings', json={
        'room_id': 1,
        'organizer_id': 1,
        'start_time': '2026-07-20T09:00:00',
        'end_time': '2026-07-20T09:30:00',
    })

    response = client.post('/bookings', json={
        'room_id': 1,
        'organizer_id': 1,
        'start_time': '2026-07-20T09:15:00',
        'end_time': '2026-07-20T09:45:00',
    })

    assert response.status_code == 409
    body = response.get_json()
    assert body['data'] is None
    assert 'conflict' in body['error'].lower()


def test_get_bookings_success(client):
    """GET /bookings lists all bookings, optionally filtered by room_id/organizer_id."""
    client.post('/bookings', json={
        'room_id': 1, 'organizer_id': 1,
        'start_time': '2026-07-20T09:00:00', 'end_time': '2026-07-20T09:30:00',
    })
    client.post('/bookings', json={
        'room_id': 1, 'organizer_id': 1,
        'start_time': '2026-07-20T10:00:00', 'end_time': '2026-07-20T10:30:00',
    })

    response = client.get('/bookings')

    assert response.status_code == 200
    body = response.get_json()
    assert body['error'] is None
    assert len(body['data']) == 2


def test_get_bookings_filtered_by_nonexistent_room_returns_empty_list(client):
    """GET /bookings has no error branch in the route (it never returns 4xx/5xx);
    filtering by a room_id with no matching bookings is the closest equivalent
    "nothing found" case and still returns 200 with an empty list."""
    client.post('/bookings', json={
        'room_id': 1, 'organizer_id': 1,
        'start_time': '2026-07-20T09:00:00', 'end_time': '2026-07-20T09:30:00',
    })

    response = client.get('/bookings', query_string={'room_id': 999})

    assert response.status_code == 200
    body = response.get_json()
    assert body['data'] == []


def test_reschedule_booking_success(client):
    """PUT /bookings/<id> updates the booking's time slot and returns 200."""
    create_resp = client.post('/bookings', json={
        'room_id': 1, 'organizer_id': 1,
        'start_time': '2026-07-20T09:00:00', 'end_time': '2026-07-20T09:30:00',
    })
    booking_id = create_resp.get_json()['data']['id']

    response = client.put(f'/bookings/{booking_id}', json={
        'start_time': '2026-07-20T11:00:00',
        'end_time': '2026-07-20T11:30:00',
    })

    assert response.status_code == 200
    body = response.get_json()
    assert body['data']['start_time'] == '2026-07-20T11:00:00'
    assert body['data']['end_time'] == '2026-07-20T11:30:00'


def test_reschedule_booking_not_found_returns_404(client):
    """PUT /bookings/<id> for a booking ID that doesn't exist returns 404."""
    response = client.put('/bookings/999', json={
        'start_time': '2026-07-20T11:00:00',
        'end_time': '2026-07-20T11:30:00',
    })

    assert response.status_code == 404
    body = response.get_json()
    assert body['data'] is None
    assert body['error'] == 'Booking not found'


def test_cancel_booking_success(client):
    """DELETE /bookings/<id> soft-cancels the booking (status='cancelled') and returns 200."""
    create_resp = client.post('/bookings', json={
        'room_id': 1, 'organizer_id': 1,
        'start_time': '2026-07-20T09:00:00', 'end_time': '2026-07-20T09:30:00',
    })
    booking_id = create_resp.get_json()['data']['id']

    response = client.delete(f'/bookings/{booking_id}')

    assert response.status_code == 200
    body = response.get_json()
    assert body['data']['status'] == 'cancelled'

    # soft delete: the booking still exists, just marked cancelled
    get_resp = client.get(f'/bookings/{booking_id}')
    assert get_resp.status_code == 200
    assert get_resp.get_json()['data']['status'] == 'cancelled'


def test_cancel_booking_not_found_returns_404(client):
    """DELETE /bookings/<id> for a booking ID that doesn't exist returns 404."""
    response = client.delete('/bookings/999')

    assert response.status_code == 404
    body = response.get_json()
    assert body['data'] is None
    assert body['error'] == 'Booking not found'
