from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def create_app():
    """Create and configure the Flask application instance.

    Application factory that instantiates the Flask app, points
    SQLAlchemy at the SQLite database under ``db/bookings.db``,
    registers the ``bookings`` and ``rooms`` blueprints, and creates
    all database tables if they do not already exist.

    Args:
        None

    Returns:
        flask.Flask: A fully configured Flask application instance,
        ready to be run (``app.run()``) or served by a WSGI server.

    Examples:
        Example 1 - create and run the app directly::

            from app import create_app
            app = create_app()
            app.run(debug=True)

        Example 2 - create the app for use in a test client::

            from app import create_app
            app = create_app()
            client = app.test_client()
            response = client.get('/health')

    Note:
        This is a Python factory function, not an HTTP route, so it
        has no browser or curl equivalent.
    """
    app = Flask(__name__)
    base_dir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'db', 'bookings.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'workshop-secret-key'

    db.init_app(app)

    from routes.bookings import bookings_bp
    from routes.rooms import rooms_bp
    app.register_blueprint(bookings_bp)
    app.register_blueprint(rooms_bp)

    @app.route('/health')
    def health():
        """Health check endpoint for the service.

        Route:
            GET /health

        Lightweight endpoint used to verify that the Flask application
        is running and able to respond to requests. Useful for load
        balancer or uptime-monitoring checks.

        Args:
            None. Takes no path, query, or body parameters.

        Returns:
            dict: JSON object with the following keys:
                status (str): Always ``'ok'`` when the service is reachable.
                service (str): Service name, ``'conference-room-booking'``.

        Examples:
            Example 1 - Python requests::

                import requests
                response = requests.get('http://localhost:5000/health')
                print(response.json())
                # {'status': 'ok', 'service': 'conference-room-booking'}

            Example 2 - JavaScript fetch::

                fetch('http://localhost:5000/health')
                  .then(res => res.json())
                  .then(data => console.log(data));

            Browser:
                Navigate to http://localhost:5000/health

            cURL:
                curl -X GET http://localhost:5000/health
        """
        return {'status': 'ok', 'service': 'conference-room-booking'}

    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
