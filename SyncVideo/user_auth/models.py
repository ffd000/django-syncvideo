from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.db import models
from django.contrib.auth import models as auth_models

from SyncVideo.user_auth.manager import AppUserManager
from SyncVideo.user_auth.validators import validate_only_alphanum_and_underscores


class AppUser(auth_models.AbstractBaseUser, auth_models.PermissionsMixin):
    MAX_LEN_USERNAME = 30
    MIN_LEN_USERNAME = 3

    username = models.CharField(
        max_length=MAX_LEN_USERNAME,
        unique=True,
        validators=(
            MinLengthValidator(MIN_LEN_USERNAME),
            MaxLengthValidator(MAX_LEN_USERNAME),
            validate_only_alphanum_and_underscores
        ),
    )

    email = models.EmailField()

    is_staff = models.BooleanField(
        default=False,
    )

    USERNAME_FIELD = 'username'
    objects = AppUserManager()
