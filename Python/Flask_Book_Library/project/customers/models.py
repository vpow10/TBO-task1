from sqlalchemy.orm import validates

from project import db, app
from project.validation import LETTERS, validate_text, validate_int


CUSTOMER_NAME_CHARS = LETTERS + r" '\-"
CITY_CHARS = LETTERS + r' \-'


# Customer model
class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    city = db.Column(db.String(64))
    age = db.Column(db.Integer)

    def __init__(self, name, city, age):
        self.name = name
        self.city = city
        self.age = age

    @validates('name')
    def validate_name(self, key, value):
        return validate_text('name', value, CUSTOMER_NAME_CHARS)

    @validates('city')
    def validate_city(self, key, value):
        return validate_text('city', value, CITY_CHARS)

    @validates('age')
    def validate_age(self, key, value):
        return validate_int('age', value, 1, 120)

    def __repr__(self):
        return f"Customer(ID: {self.id}, Name: {self.name}, City: {self.city}, Age: {self.age})"


with app.app_context():
    db.create_all()
