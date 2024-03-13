from django.core.exceptions import ValidationError
import re

def latin_and_spaces_validator(value):
    if not re.match(r'^[A-Za-z ]+$', value):
        raise ValidationError("Only Latin characters and spaces are allowed.")
