"""Production WSGI entrypoint.

Gunicorn's eventlet worker monkey-patches stdlib before importing this module,
so we can just build the app and expose it.
"""
from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
