import sys
import os
from django.db import transaction

# Добавляем путь к корневой директории проекта в sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

from django.test import TestCase, override_settings
from django.urls import reverse
from users.models import CustomUser  # Абсолютный импорт
from .forms import RegistrationForm
from hypothesis import given, settings, strategies as st
from hypothesis.extra.django import TestCase as HypTestCase

@override_settings(ROOT_URLCONF='flower_shop.flower_shop.urls')
class UserRegistrationTests(TestCase):
    def test_valid_registration(self):
        response = self.client.post(reverse('users:register'), {
            'username': 'newuser',
            'email': 'user@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'phone': '+79123456789',
            'address': 'Test Address'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CustomUser.objects.count(), 1)

    def test_password_mismatch(self):
        response = self.client.post(reverse('users:register'), {
            'username': 'baduser',
            'email': 'bad@example.com',
            'password1': 'Pass123!',
            'password2': 'WrongPass456!',
            'phone': '+79123456789',
            'address': 'Test Address'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertIn('password2', form.errors)
        self.assertEqual(
            form.errors['password2'],
            ['Введенные пароли не совпадают.']
        )

@override_settings(ROOT_URLCONF='flower_shop.flower_shop.urls')
class ProfileTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username="profileuser", password="testpass")

    def test_profile_access(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('users:profile'))
        self.assertContains(response, "profileuser")

    def test_profile_update(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('users:profile_edit'), {
            'username': 'updateduser',
            'email': 'updated@example.com',
            'phone': '+79999999999',
            'address': 'New Address'
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'updated@example.com')

@override_settings(ROOT_URLCONF='flower_shop.flower_shop.urls')
class UserHypothesisTests(HypTestCase):
    @settings(deadline=None)
    @given(
        username=st.from_regex(r"^[a-zA-Z0-9]{4,25}$", fullmatch=True),
        phone=st.builds(lambda x: f"+7{x:010d}", st.integers(min_value=0, max_value=10**10-1))
    )
    def test_user_creation_properties(self, username, phone):
        with transaction.atomic():
            CustomUser.objects.all().delete()
        user = CustomUser.objects.create_user(
            username=username,
            password="testpass",
            phone=phone
        )
        self.assertEqual(user.username, username)
        self.assertEqual(user.phone, phone)