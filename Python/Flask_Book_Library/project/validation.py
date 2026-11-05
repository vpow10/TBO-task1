import re
from datetime import date


# Latin letters including Polish diacritics (Latin-1 Supplement + Latin Extended-A)
LETTERS = 'A-Za-zÀ-ÖØ-öø-ÿĀ-ž'


def validate_text(field, value, allowed_chars, max_length=64):
    if not isinstance(value, str):
        raise ValueError(f'{field} must be a string')

    value = value.strip()
    if not 1 <= len(value) <= max_length:
        raise ValueError(f'{field} must be between 1 and {max_length} characters long')

    if not re.fullmatch(f'[{allowed_chars}]+', value):
        raise ValueError(f'{field} contains forbidden characters')

    return value


def validate_int(field, value, min_value, max_value):
    if isinstance(value, bool):
        raise ValueError(f'{field} must be an integer')

    if isinstance(value, str) and re.fullmatch(r'\d{1,4}', value.strip()):
        value = int(value)

    if not isinstance(value, int):
        raise ValueError(f'{field} must be an integer')

    if not min_value <= value <= max_value:
        raise ValueError(f'{field} must be between {min_value} and {max_value}')

    return value


def validate_choice(field, value, choices):
    if value not in choices:
        raise ValueError(f'{field} must be one of: {", ".join(choices)}')

    return value


def current_year():
    return date.today().year
