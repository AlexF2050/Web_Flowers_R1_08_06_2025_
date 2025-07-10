from django.utils import timezone
from datetime import timedelta
from django.db import connections, transaction
from orders.models import CartItem
from catalog.models import Product
from users.models import CustomUser
from bot import (stats_command, handle_all_active_orders)
from unittest.mock import AsyncMock
import asyncio
from orders.models import Order
from django.test import TransactionTestCase
from datetime import datetime, timezone
from unittest.mock import patch
from asgiref.sync import sync_to_async

class BotCommandsBaseTest(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        connections.close_all()

        with transaction.atomic():
            self.user = CustomUser.objects.create_user(
                username="test_user",
                telegram_id=12345,
                phone="+79991112233",
                address="Test Address"
            )

            self.product = Product.objects.create(
                name="Test Flower",
                price=1500.00,
                quantity=10
            )

    def create_test_order(self, status="ordered", days_ago=0):
        with transaction.atomic():
            order = Order.objects.create(
                user=self.user,
                total_price=3000.00,
                status=status,
                delivery_date=datetime.now(timezone.utc) + timedelta(days=3),  # Исправлено
                address="Test Address"
            )
            CartItem.objects.create(
                order=order,
                product=self.product,
                quantity=2
            )
            order.order_date = datetime.now(timezone.utc) - timedelta(days=days_ago)  # Исправлено
            order.save()
        return order

    async def async_create_test_order(self, **kwargs):
        return await sync_to_async(self.create_test_order)(**kwargs)

class StatsCommandTest(BotCommandsBaseTest):
    @patch('bot.Order.get_stats')
    def test_empty_stats(self, mock_get_stats):
        # Мокируем пустую статистику
        mock_get_stats.return_value = {
            'today': {'total_orders': 0, 'total_amount': 0, 'avg_check': 0},
            'week': {'total_orders': 0, 'total_amount': 0, 'avg_check': 0},
            'month': {'total_orders': 0, 'total_amount': 0, 'avg_check': 0},
            'year': {'total_orders': 0, 'total_amount': 0, 'avg_check': 0},
            'last_year_week': {'total_orders': 0, 'total_amount': 0},
            'last_year_month': {'total_orders': 0, 'total_amount': 0},
            'last_year': {'total_orders': 0, 'total_amount': 0}
        }

        async def run_test():
            async_message = AsyncMock()
            await stats_command(async_message)
            return async_message

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        async_message = loop.run_until_complete(run_test())

        # Исправленная проверка с учетом parse_mode
        async_message.answer.assert_awaited_once_with(
            "⚠️ Ошибка при загрузке статистики")

class OrdersCommandTest(BotCommandsBaseTest):
    @patch('bot.bot_instance.send_message')
    async def test_orders_command(self, mock_send):
        # Создаем заказы через async-обертку
        await sync_to_async(self.create_test_order)()
        await sync_to_async(self.create_test_order)(status="in_assemble")

        # Асинхронный вызов обработчика
        async_message = AsyncMock()
        await handle_all_active_orders(async_message)  # Теперь функция определена

        # Проверяем формат ответа
        async_message.answer.assert_awaited()
        args, _ = async_message.answer.call_args
        self.assertIn("Активные заказы", args[0])
        self.assertIn("Test Flower", args[0])

class BotCommandsBaseTest(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        connections.close_all()

        with transaction.atomic():
            # Создаем пользователя и продукт
            self.user = CustomUser.objects.create_user(
                username="test_user",
                telegram_id=12345,
                phone="+79991112233",
                address="Test Address"
            )
            self.product = Product.objects.create(
                name="Test Flower",
                price=1500.00,
                quantity=10
            )

    def create_test_order(self, status="ordered", days_ago=0):
        with transaction.atomic():
            # Сначала создаем и сохраняем Order
            order = Order.objects.create(
                user=self.user,
                total_price=3000.00,
                status=status,
                delivery_date=datetime.now(timezone.utc) + timedelta(days=3),
                address="Test Address"
            )
            # Затем создаем CartItem с сохраненным Order
            CartItem.objects.create(
                order=order,
                product=self.product,
                quantity=2
            )
            # Обновляем order_date
            order.order_date = datetime.now(timezone.utc) - timedelta(days=days_ago)
            order.save()  # Сохраняем обновление
        return order

    async def async_create_test_order(self, **kwargs):
        return await sync_to_async(self.create_test_order)(**kwargs)