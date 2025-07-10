import logging
from django.test import TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, ANY
from hypothesis import given, strategies as st, settings
from hypothesis.extra.django import TestCase as HypTestCase
from django.apps import apps
from django.utils import timezone
from PIL import Image, ImageDraw
import io
from django.db import transaction

img = Image.new('RGB', (450, 450), color='white')
draw = ImageDraw.Draw(img)
draw.text((10, 10), "📊", fill='black')  # Добавляем эмодзи

# Сохранение в байты
img_byte_arr = io.BytesIO()
img.save(img_byte_arr, format='JPEG')
img_bytes = img_byte_arr.getvalue()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# Получение моделей через apps.get_model для независимости от миграций
Order = apps.get_model('orders', 'Order')
Cart = apps.get_model('orders', 'Cart')
CartItem = apps.get_model('orders', 'CartItem')
Product = apps.get_model('catalog', 'Product')
CustomUser = apps.get_model('users', 'CustomUser')


@override_settings(ROOT_URLCONF='flower_shop.flower_shop.urls')
class OrderProcessingTests(TestCase):
    """Тесты основного процесса оформления заказа"""

    def setUp(self):
        # Создание тестового пользователя
        self.user = CustomUser.objects.create_user(
            username="testuser",
            password="testpass",
            phone="+79991234567",
            address="Test Address",
            email="x123@ctmol.ru"
        )

        # Создание тестового продукта с изображением
        self.product = Product.objects.create(
            name="Test Product",
            price=1000,
            quantity=10,
            image=SimpleUploadedFile('TestOrders.jpg', img_bytes, 'image/jpeg')
        )

        # Создание корзины пользователя
        self.cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)

    def test_successful_order_creation(self):
        """Тест успешного создания заказа с корректной обработкой CSRF"""
        self.client.force_login(self.user)

        # Подготовка данных с валидным временем (минимум +2 часа)
        delivery_time = timezone.localtime() + timezone.timedelta(hours=3)
        formatted_time = delivery_time.strftime('%Y-%m-%dT%H:%M')

        # Отправка POST-запроса с корректными данными
        response = self.client.post(
            reverse('orders:checkout'),
            data={
                'delivery_date': formatted_time,
                'use_profile_address': False,  # Булево значение
                'address': 'New Test Address'
            },
            follow=True
        )

        # Проверки
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.address, 'New Test Address')

@override_settings(ROOT_URLCONF='flower_shop.flower_shop.urls')
class PaymentIntegrationTests(TestCase):
    @patch('orders.views.send_telegram_notification')
    def test_notification_sending(self, mock_notification):
        """Тест отправки уведомления после успешного заказа"""
        # 1. Создание тестовых данных
        user = CustomUser.objects.create_user(
            username="tguser",
            password="testpass",
            phone="+79991234567",
            address="Valid Address",
            email="x123@ctmol.ru"
        )

        product = Product.objects.create(
            name="TG Product",
            price=2000,
            quantity=5,
            image=SimpleUploadedFile('TestOrders.jpg', img_bytes, 'image/jpeg')
        )

        # 2. Создание корзины
        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, product=product, quantity=1)

        # 3. Авторизация и оформление заказа
        self.client.force_login(user)
        delivery_time = timezone.localtime() + timezone.timedelta(hours=3)
        response = self.client.post(
            reverse('orders:checkout'),
            data={
                'delivery_date': delivery_time.strftime('%Y-%m-%dT%H:%M'),
                'use_profile_address': True
            },
            follow=True
        )

        # 4. Проверка создания заказа
        self.assertEqual(Order.objects.count(), 1, "Заказ не создан")
        order = Order.objects.first()

        # 5. Проверка вызова уведомления
        # Исправление: передаем объект заказа вместо order_id и user_id
        mock_notification.assert_called_once_with(order)

@override_settings(ROOT_URLCONF='flower_shop.flower_shop.urls')
class OrderHypothesisTests(HypTestCase):
    """Property-based тесты с использованием Hypothesis"""

    @given(
        quantity=st.integers(min_value=1, max_value=5),
        price=st.integers(min_value=100, max_value=10000)
    )
    @settings(max_examples=10, deadline=None)  # Отключаем проверку времени выполнения

    def test_order_creation_with_various_values(self, quantity, price):
        """Тест создания заказов с различными параметрами"""
        with transaction.atomic():
            user = CustomUser.objects.create_user(
            username=f"hypuser-{price}-{quantity}",
            password="testpass",
            phone="+79991234567",
            address="Test Address",
            email="x123@ctmol.ru"
            )

            product = Product.objects.create(
                name=f"HypProduct-{price}",
                price=price,
                quantity=quantity + 100,  # Гарантируем достаточное количество
                image=SimpleUploadedFile('TestOrders.jpg', img_bytes, 'image/jpeg')
            )

            cart = Cart.objects.create(user=user)
            CartItem.objects.create(cart=cart, product=product, quantity=quantity)

            self.client.force_login(user)
            delivery_time = timezone.localtime() + timezone.timedelta(hours=3, minutes=1)

            response = self.client.post(
                reverse('orders:checkout'),
                data={
                    'delivery_date': delivery_time.strftime('%Y-%m-%dT%H:%M'),
                    'use_profile_address':False,
                    'address': 'Hypothesis Test Address'
                },
                follow=True
            )

            # Основные проверки
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                Order.objects.count(), 1,
                f"Ошибка при quantity={quantity}, price={price}. Ответ: {response.content.decode()}"
            )

            # Проверка корректности расчета суммы
            order = Order.objects.first()
            self.assertEqual(
                order.total_price,
                price * quantity,
                f"Неверная сумма заказа: {price} * {quantity} ≠ {order.total_price}"
            )

    def tearDown(self):
        """Очистка данных после каждого теста"""
        # Удаляем объекты из БД
        Order.objects.all().delete()
        CartItem.objects.all().delete()
        Cart.objects.all().delete()
        Product.objects.all().delete()
        CustomUser.objects.all().delete()

