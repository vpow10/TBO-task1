import os

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

import pytest

from project import app as flask_app, db
from project.books.models import Book
from project.customers.models import Customer
from project.loans.models import Loan


@pytest.fixture
def app():
    flask_app.config['TESTING'] = True
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.rollback()
        Book.query.delete()
        Customer.query.delete()
        Loan.query.delete()
        db.session.commit()


@pytest.fixture
def client(app):
    return app.test_client()
