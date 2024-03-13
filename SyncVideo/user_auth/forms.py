from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.core.validators import MinLengthValidator
# from SyncVideo.user_auth.models import UserProfile
from django.contrib.auth import forms as auth_forms, get_user_model
from django.forms import PasswordInput

from SyncVideo.rooms.models import Room
from SyncVideo.user_auth.models import AppUser
from SyncVideo.user_auth.validators import validate_only_letters
# from SyncVideo.user_auth.common.custom_mixins import BootstrapFormMixin


UserModel = get_user_model()

class ProfileCreateForm(auth_forms.UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = get_user_model()
        fields = ["username", "email", "password1", "password2"]

    # first_name = forms.CharField(
    #     max_length=UserProfile.FIRST_NAME_MAX_LEN,
    #     validators=(
    #         MinLengthValidator(UserProfile.FIRST_NAME_MIN_LEN),
    #         validate_only_letters,
    #     ),
    # )
    #
    # last_name = forms.CharField(
    #     max_length=UserProfile.LAST_NAME_MAX_LEN,
    #     validators=(
    #         MinLengthValidator(UserProfile.FIRST_NAME_MIN_LEN),
    #         validate_only_letters,
    #     ),
    # )


    def save(self, commit=True):
        user = super().save(commit=commit)

        return user


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['username', 'email']


# class PasswordChangeForm(auth_forms.PasswordChangeForm):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['old_password'].widget = forms.PasswordInput(attrs={'class': 'form-control'})
#         self.fields['new_password'].widget = forms.PasswordInput(attrs={'class': 'form-control'})
#         self.fields['new_password_repeat'].widget = forms.PasswordInput(attrs={'class': 'form-control'})
#
#         super(PasswordChangeForm, self).__init__(*args, **kwargs)


class UserUpdateForm(UserChangeForm):
    class Meta:
        model = AppUser
        fields = ['username', 'email']


class DeleteProfileForm(forms.Form):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.user.check_password(password):
            raise forms.ValidationError('Invalid password')
        return password

    def confirm_delete(self):
        return True
