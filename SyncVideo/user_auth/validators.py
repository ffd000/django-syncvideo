from django.core.exceptions import ValidationError
import re

ERROR_ONLY_ALPHANUM_UNDERSCORE = "This value can only contain letters, numbers, and underscores."
ERROR_ONLY_LETTERS = "This value can only contain only letters."

def validate_only_alphanum_and_underscores(value):
    if not re.match(r'^[A-Za-z0-9_@]+$', value):
        raise ValidationError(ERROR_ONLY_ALPHANUM_UNDERSCORE)
    return value


def validate_only_letters(value):
    for i in value:
        if not i.isalpha():
            raise ValidationError(ERROR_ONLY_LETTERS)
    return value
