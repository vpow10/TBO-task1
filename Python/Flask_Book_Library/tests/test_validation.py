from datetime import date

import pytest

from project import db
from project.books.models import Book
from project.customers.models import Customer
from project.loans.models import Loan
from project.validation import current_year


XSS_PAYLOADS = [
    '<script>alert(1)</script>',
    '<img src=x onerror=alert(1)>',
    '<svg onload=alert(1)>',
    '"><script>alert(1)</script>',
    '&lt;script&gt;alert(1)&lt;/script&gt;',
    '`${alert(1)}`',
]


def make_book(**overrides):
    data = {'name': 'Pan Tadeusz', 'author': 'Adam Mickiewicz', 'year_published': 1834, 'book_type': '2days'}
    data.update(overrides)
    return Book(**data)


def make_customer(**overrides):
    data = {'name': 'Jan Kowalski', 'city': 'Warszawa', 'age': 30}
    data.update(overrides)
    return Customer(**data)


def make_loan(**overrides):
    data = {
        'customer_name': 'Jan Kowalski', 'book_name': 'Lalka', 'loan_date': date(2024, 1, 1), 'return_date': date(2024, 1, 10),
        'original_author': 'Bolesław Prus', 'original_year_published': 1890, 'original_book_type': '5days',
    }
    data.update(overrides)
    return Loan(**data)


class TestBookModel:

    @pytest.mark.parametrize('name', ['Pan Tadeusz', 'Ogniem i mieczem', 'Harry Potter (tom 1)', '1984', 'Lalka: wydanie II, poprawione!', "Harry Potter and the Philosopher's Stone"])
    def test_valid_name(self, name):
        assert make_book(name=name).name == name

    @pytest.mark.parametrize('author', ['Adam Mickiewicz', 'Henryk Sienkiewicz', "Flannery O'Connor", 'J.R.R. Tolkien', 'Jean-Paul Sartre', 'Żeromski Stefan'])
    def test_valid_author(self, author):
        assert make_book(author=author).author == author

    def test_strips_whitespace(self):
        book = make_book(name='  Lalka  ', author=' Bolesław Prus ')
        assert book.name == 'Lalka'
        assert book.author == 'Bolesław Prus'

    @pytest.mark.parametrize('payload', XSS_PAYLOADS)
    def test_rejects_xss_in_name(self, payload):
        with pytest.raises(ValueError):
            make_book(name=payload)

    @pytest.mark.parametrize('payload', XSS_PAYLOADS)
    def test_rejects_xss_in_author(self, payload):
        with pytest.raises(ValueError):
            make_book(author=payload)

    @pytest.mark.parametrize('value', ['', '   ', 'a' * 65, None, 123])
    def test_rejects_invalid_name(self, value):
        with pytest.raises(ValueError):
            make_book(name=value)

    def test_rejects_digits_in_author(self):
        with pytest.raises(ValueError):
            make_book(author='Agent 007')

    @pytest.mark.parametrize('year', [1, 1834, '2001', current_year()])
    def test_valid_year(self, year):
        assert make_book(year_published=year).year_published == int(year)

    @pytest.mark.parametrize('year', [0, -5, current_year() + 1, 'abc', '<script>', None, 2001.5, True])
    def test_rejects_invalid_year(self, year):
        with pytest.raises(ValueError):
            make_book(year_published=year)

    @pytest.mark.parametrize('book_type', ['2days', '5days', '10days'])
    def test_valid_book_type(self, book_type):
        assert make_book(book_type=book_type).book_type == book_type

    @pytest.mark.parametrize('book_type', ['1day', '', None, '<b>2days</b>'])
    def test_rejects_invalid_book_type(self, book_type):
        with pytest.raises(ValueError):
            make_book(book_type=book_type)

    @pytest.mark.parametrize('status', ['available', 'loaned'])
    def test_valid_status(self, status):
        assert make_book(status=status).status == status

    @pytest.mark.parametrize('status', ['', 'lost', None, '<script>alert(1)</script>'])
    def test_rejects_invalid_status(self, status):
        with pytest.raises(ValueError):
            make_book(status=status)

    def test_rejects_xss_on_update(self):
        book = make_book()
        with pytest.raises(ValueError):
            book.author = '<img src=x onerror=alert(1)>'
        assert book.author == 'Adam Mickiewicz'


class TestCustomerModel:

    @pytest.mark.parametrize('name', ['Jan Kowalski', 'Anna Nowak-Kowalska', "Seán O'Brien", 'Łucja Żółć'])
    def test_valid_name(self, name):
        assert make_customer(name=name).name == name

    @pytest.mark.parametrize('city', ['Warszawa', 'Bielsko-Biała', 'Zielona Góra', 'Łódź'])
    def test_valid_city(self, city):
        assert make_customer(city=city).city == city

    @pytest.mark.parametrize('payload', XSS_PAYLOADS)
    def test_rejects_xss_in_name(self, payload):
        with pytest.raises(ValueError):
            make_customer(name=payload)

    @pytest.mark.parametrize('payload', XSS_PAYLOADS)
    def test_rejects_xss_in_city(self, payload):
        with pytest.raises(ValueError):
            make_customer(city=payload)

    @pytest.mark.parametrize('name', ['', '   ', 'a' * 65, None, 'Jan 2'])
    def test_rejects_invalid_name(self, name):
        with pytest.raises(ValueError):
            make_customer(name=name)

    @pytest.mark.parametrize('city', ['', 'Warszawa 1', 'a' * 65, None, "javascript:alert('x')"])
    def test_rejects_invalid_city(self, city):
        with pytest.raises(ValueError):
            make_customer(city=city)

    def test_rejects_xss_on_update(self):
        customer = make_customer()
        with pytest.raises(ValueError):
            customer.city = '<svg onload=alert(1)>'
        assert customer.city == 'Warszawa'

    @pytest.mark.parametrize('age', [1, 30, '45', 120])
    def test_valid_age(self, age):
        assert make_customer(age=age).age == int(age)

    @pytest.mark.parametrize('age', [0, 121, -1, 'abc', '30<script>', None, True])
    def test_rejects_invalid_age(self, age):
        with pytest.raises(ValueError):
            make_customer(age=age)


class TestBookEndpoints:

    def test_create_valid_book(self, client):
        response = client.post('/books/create', json={'name': 'Lalka', 'author': 'Bolesław Prus', 'year_published': '1890', 'book_type': '5days'})
        assert response.status_code == 302
        assert Book.query.filter_by(name='Lalka').count() == 1

    def test_create_book_with_xss_is_rejected(self, client):
        response = client.post('/books/create', json={'name': 'XSS Test Book', 'author': '<img src=x onerror=alert(1)>', 'year_published': '2024', 'book_type': '2days'})
        assert response.status_code == 400
        assert Book.query.count() == 0

    def test_create_book_with_missing_fields_is_rejected(self, client):
        response = client.post('/books/create', json={'name': 'Lalka'})
        assert response.status_code == 400

    def test_edit_book_with_xss_is_rejected(self, client):
        client.post('/books/create', json={'name': 'Lalka', 'author': 'Bolesław Prus', 'year_published': 1890, 'book_type': '5days'})
        book = Book.query.filter_by(name='Lalka').first()

        response = client.post(f'/books/{book.id}/edit', json={'author': '<script>alert(1)</script>'})

        assert response.status_code == 400
        assert db.session.get(Book, book.id).author == 'Bolesław Prus'

    @pytest.mark.parametrize('body', ['not json', 'null', '[]'])
    def test_edit_book_with_invalid_json_is_rejected(self, client, body):
        client.post('/books/create', json={'name': 'Lalka', 'author': 'Bolesław Prus', 'year_published': 1890, 'book_type': '5days'})
        book = Book.query.filter_by(name='Lalka').first()

        response = client.post(f'/books/{book.id}/edit', data=body, content_type='application/json')

        assert response.status_code == 400


class TestCustomerEndpoints:

    def test_create_valid_customer(self, client):
        response = client.post('/customers/create', data={'name': 'Jan Kowalski', 'city': 'Kraków', 'age': '30'})
        assert response.status_code == 302
        assert Customer.query.filter_by(name='Jan Kowalski').count() == 1

    def test_create_customer_with_xss_is_rejected(self, client):
        response = client.post('/customers/create', data={'name': 'Jan Kowalski', 'city': '<svg onload=alert(1)>', 'age': '30'})
        assert response.status_code == 400
        assert Customer.query.count() == 0

    def test_edit_customer_with_xss_is_rejected(self, client):
        client.post('/customers/create', data={'name': 'Jan Kowalski', 'city': 'Kraków', 'age': '30'})
        customer = Customer.query.filter_by(name='Jan Kowalski').first()

        response = client.post(f'/customers/{customer.id}/edit', data={'name': '<script>alert(1)</script>', 'city': 'Kraków', 'age': '30'})

        assert response.status_code == 400
        assert db.session.get(Customer, customer.id).name == 'Jan Kowalski'


class TestLoanModel:

    def test_valid_loan(self):
        loan = make_loan()
        assert loan.customer_name == 'Jan Kowalski'
        assert loan.book_name == 'Lalka'

    @pytest.mark.parametrize('field', ['customer_name', 'book_name', 'original_author'])
    @pytest.mark.parametrize('payload', XSS_PAYLOADS)
    def test_rejects_xss_in_text_fields(self, field, payload):
        with pytest.raises(ValueError):
            make_loan(**{field: payload})

    @pytest.mark.parametrize('overrides', [
        {'original_year_published': 0},
        {'original_book_type': '<b>2days</b>'},
        {'loan_date': None},
        {'return_date': '2024-01-10'},
    ])
    def test_rejects_invalid_values(self, overrides):
        with pytest.raises(ValueError):
            make_loan(**overrides)


class TestLoanEndpoints:

    @pytest.fixture
    def book_and_customer(self, client):
        client.post('/books/create', json={'name': 'Lalka', 'author': 'Bolesław Prus', 'year_published': 1890, 'book_type': '5days'})
        client.post('/customers/create', data={'name': 'Jan Kowalski', 'city': 'Kraków', 'age': '30'})

    def test_create_valid_loan(self, client, book_and_customer):
        response = client.post('/loans/create', data={'customer_name': 'Jan Kowalski', 'book_name': 'Lalka', 'loan_date': '2024-01-01', 'return_date': '2024-01-10'})
        assert response.status_code == 302
        assert Loan.query.filter_by(customer_name='Jan Kowalski', book_name='Lalka').count() == 1

    def test_create_loan_with_xss_customer_name_is_rejected(self, client, book_and_customer):
        response = client.post('/loans/create', data={'customer_name': '<img src=x onerror=alert(1)>', 'book_name': 'Lalka', 'loan_date': '2024-01-01', 'return_date': '2024-01-10'})
        assert response.status_code == 400
        assert Loan.query.count() == 0
        assert Book.query.filter_by(name='Lalka').count() == 1

    def test_create_loan_for_unknown_customer_is_rejected(self, client, book_and_customer):
        response = client.post('/loans/create', data={'customer_name': 'Anna Nowak', 'book_name': 'Lalka', 'loan_date': '2024-01-01', 'return_date': '2024-01-10'})
        assert response.status_code == 400
        assert Loan.query.count() == 0

    def test_create_loan_with_invalid_date_is_rejected(self, client, book_and_customer):
        response = client.post('/loans/create', data={'customer_name': 'Jan Kowalski', 'book_name': 'Lalka', 'loan_date': 'jutro', 'return_date': '2024-01-10'})
        assert response.status_code == 400
        assert Loan.query.count() == 0
