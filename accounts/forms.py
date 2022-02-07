from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, required=False, help_text='Optional. Allows for password recovery.')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', )