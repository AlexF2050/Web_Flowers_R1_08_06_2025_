from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model  # Используем get_user_model

# Получаем модель текущего пользователя
User = get_user_model()

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label=_('Электронная почта'),
        required=True
    )
    phone = forms.CharField(
        label=_('Телефон'),
        max_length=20,
        required=True
    )
    address = forms.CharField(
        label=_('Адрес ДОСТАВКИ'),
        widget=forms.Textarea,
        required=True
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'phone', 'address')
        labels = {
            'username': _('Имя пользователя'),
            'password1': _('Пароль'),
            'password2': _('Подтверждение пароля'),
        }
        help_texts = {
            'username': _('Только буквы, цифры и символы @/./+/-/_'),
        }

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'address']
        labels = {
            'username': 'Логин',
            'email': 'Электронная почта',
            'phone': 'Телефон',
            'address': 'Адрес ДОСТАВКИ'
        }