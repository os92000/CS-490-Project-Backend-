import pytest
from app import create_app
from models import db


@pytest.fixture
def app():
    app = create_app("testing")

    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "s8F!xP9@kL2#zQ7$mT4^vW1&bR6*YhN3"
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()