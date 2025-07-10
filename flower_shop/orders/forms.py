# orders/forms.py
from django import forms
from django.utils import timezone

class DeliveryDateForm(forms.Form):
    delivery_date = forms.DateTimeField(
        label='Дата и время доставки',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        help_text='Минимальное время доставки - через 2 часа от текущего момента',
        initial=timezone.now() + timezone.timedelta(hours=2)
    )

    def clean_delivery_date(self):
        data = self.cleaned_data['delivery_date']
        now = timezone.now()

        if data < now + timezone.timedelta(hours=2):
            raise forms.ValidationError("Доставка возможна не ранее чем через 2 часа")

        return data

# Новая форма для адреса
class DeliveryAddressForm(forms.Form):
    USE_PROFILE_ADDRESS_CHOICES = (
        (True, 'Использовать адрес из профиля'),
        (False, 'Указать другой адрес'),
    )

    use_profile_address = forms.TypedChoiceField(
        label='Выбор адреса',  # Исправьте label на что-то осмысленное
        choices=USE_PROFILE_ADDRESS_CHOICES,
        coerce=lambda x: x == 'True',  # Оставьте, если значения 'True'/'False'
        widget=forms.RadioSelect(attrs={'class': 'radio-select'}),
        initial=False
    )

    address = forms.CharField(
        label='Новый адрес',
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Введите полный адрес доставки'
        })
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        profile_address = user.address or "Не указан"
        self.fields['use_profile_address'].choices = [
            (True, f'Использовать адрес из профиля: {profile_address}'),
            (False, 'Указать другой адрес')
        ]

    def clean(self):
        cleaned_data = super().clean()
        use_profile = cleaned_data.get('use_profile_address')
        custom_address = cleaned_data.get('address')

        if not use_profile and not custom_address:
            raise forms.ValidationError("Укажите адрес доставки")

        if use_profile and not self.user.address:
            raise forms.ValidationError("В вашем профиле не указан адрес")

        return cleaned_data