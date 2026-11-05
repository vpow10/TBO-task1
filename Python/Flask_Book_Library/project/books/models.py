from sqlalchemy.orm import validates

from project import db, app
from project.validation import LETTERS, validate_text, validate_int, validate_choice, current_year


BOOK_NAME_CHARS = LETTERS + r"0-9 .,:!?()'\-"
AUTHOR_CHARS = LETTERS + r" .'\-"
BOOK_TYPES = ('2days', '5days', '10days')
BOOK_STATUSES = ('available', 'loaned')


# Book model
class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    author = db.Column(db.String(64))
    year_published = db.Column(db.Integer) 
    book_type = db.Column(db.String(20))
    status = db.Column(db.String(20), default='available')

    def __init__(self, name, author, year_published, book_type, status='available'):
        self.name = name
        self.author = author
        self.year_published = year_published
        self.book_type = book_type
        self.status = status

    @validates('name')
    def validate_name(self, key, value):
        return validate_text('name', value, BOOK_NAME_CHARS)

    @validates('author')
    def validate_author(self, key, value):
        return validate_text('author', value, AUTHOR_CHARS)

    @validates('year_published')
    def validate_year_published(self, key, value):
        return validate_int('year_published', value, 1, current_year())

    @validates('book_type')
    def validate_book_type(self, key, value):
        return validate_choice('book_type', value, BOOK_TYPES)

    @validates('status')
    def validate_status(self, key, value):
        return validate_choice('status', value, BOOK_STATUSES)

    def __repr__(self):
        return f"Book(ID: {self.id}, Name: {self.name}, Author: {self.author}, Year Published: {self.year_published}, Type: {self.book_type}, Status: {self.status})"


with app.app_context():
    db.create_all()