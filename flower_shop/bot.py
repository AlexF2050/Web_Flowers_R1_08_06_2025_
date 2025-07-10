import os
import sys
import django

############################ 08 06 2025
# Определяем базовую директорию (где находится bot.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Указываем путь к папке с settings.py (ваш основной пакет Django)
sys.path.append(os.path.join(BASE_DIR, "flower_shop"))  # Если settings.py в flower_shop/

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "flower_shop.settings")
django.setup()  # Теперь Django инициализирован
############################ 08 06 2025

import platform
from PIL import Image, ImageDraw, ImageFont
import tempfile

django.setup()

from aiogram import Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from asgiref.sync import sync_to_async
from orders.models import Order
from django.contrib.auth import get_user_model

import asyncio

import logging
from aiogram import Bot
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from decimal import Decimal

if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

User = get_user_model()
logger = logging.getLogger(__name__)

STATUS_MAPPING = {
    "🆕 Заказано": "ordered",
    "🔧 Собирается": "in_assemble",
    "✅ Собрано": "assembled",
    "🚚 Едет": "in_delivery - Едет",
    "📦 Доставлено": "delivered",
    "❌ Отменен": "canceled",
}

def split_text(text: str, max_length: int = 4096) -> list:
    """Разбивает текст на части по max_length символов, не разрывая строки."""
    parts = []
    while text:
        if len(text) <= max_length:
            parts.append(text)
            break
        part = text[:max_length]
        split_at = part.rfind('\n') or part.rfind(' ')
        if split_at == -1:
            split_at = max_length
        parts.append(text[:split_at])
        text = text[split_at:].lstrip()
    return parts

class OrderStatus(StatesGroup):
    waiting_for_status = State()
    waiting_for_order_id = State()

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.answer("Добро пожаловать! Используйте /help для списка команд")

@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    help_text = """
Доступные команды:
/start - Запуск бота
/orders - Список заказов
/status - Изменить статус заказа
/stats - Статистика
/help - Помощь
"""
    await message.answer(help_text)

@dp.message_handler(commands=['status'])
async def status_command(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for status in STATUS_MAPPING.keys():
        keyboard.add(status)
    await OrderStatus.waiting_for_status.set()
    await message.answer("Выберите статус:", reply_markup=keyboard)

@dp.message_handler(state=OrderStatus.waiting_for_status)
async def process_status(message: types.Message, state: FSMContext):
    if message.text not in STATUS_MAPPING:
        await message.answer("Пожалуйста, выберите статус из предложенных")
        return

    await state.update_data(status=STATUS_MAPPING[message.text])
    await OrderStatus.next()
    await message.answer("Введите номер заказа:", reply_markup=types.ReplyKeyboardRemove())

@dp.message_handler(state=OrderStatus.waiting_for_order_id)
async def process_order_id(message: types.Message, state: FSMContext):
    try:
        order_id = int(message.text)
        data = await state.get_data()
        status = data['status']

        order = await sync_to_async(Order.objects.get)(id=order_id)
        order.status = status
        await sync_to_async(order.save)()

        await message.answer(f"✅ Статус заказа #{order_id} изменен на {status}")
    except Order.DoesNotExist:
        await message.answer("❌ Заказ не найден")
    except ValueError:
        await message.answer("❌ Некорректный номер заказа")
    finally:
        await state.finish()

@dp.message_handler(commands=['orders'])
async def handle_all_active_orders(message: types.Message):
    """Вывод активных заказов (исключая Доставлено и Отменено)"""
    try:
        orders = await sync_to_async(list)(
            Order.objects.exclude(status__in=['delivered', 'canceled'])
                .select_related('user')
                .prefetch_related('cartitem_set__product')  # Добавляем оптимизацию
                .order_by('-order_date')
        )

        if not orders:
            await message.answer("📭 Активных заказов нет")
            return

        response = ["*📌 Активные заказы:*\n"]

        for order in orders:
            delivery_date = order.delivery_date.strftime('%d.%m.%Y %H:%M') if order.delivery_date else "Не указана"
            status = order.get_status_display()
            username = order.user.username if order.user else "Неизвестный пользователь"
            phone = order.user.phone if order.user and order.user.phone else "Не указан"
            address = order.user.address if order.user and order.user.address else "Не указан"

            # Формируем состав заказа
            items = await sync_to_async(list)(order.cartitem_set.all())
            order_items = []
            for item in items:
                item_total = item.product.price * item.quantity
                order_items.append(
                    f"• {item.product.name}\n"
                    f"  {item.quantity} × {item.product.price} ₽ = {item_total} ₽"
                )

            order_info = [
                f"*🆔 Заказ* `#{order.id}`",
                f"*📅 Дата заказа:* {order.order_date.strftime('%d.%m.%Y %H:%M')}",
                f"*📦 План доставки:* {delivery_date}",
                f"*🚚 Статус:* {status}",
                f"*💵 Сумма:* {order.total_price} ₽",
                f"*👤 Клиент:* {username}",
                f"*📱 Телефон:* {phone}",
                f"📱 *Адрес доставки:* {order.address}",
                f"\n*📦 Состав заказа:*\n" + "\n".join(order_items) if order_items else "*🛒 Корзина пуста*"
            ]

            response.extend(order_info)
            response.append("\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n")

        full_text = "\n".join(response)
        for part in split_text(full_text):
            await message.answer(part, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Ошибка: {str(e)}", exc_info=True)
        await message.answer("⚠️ Ошибка при загрузке данных")

async def on_startup(dp):
    await bot.set_my_commands([
        types.BotCommand("start", "Запуск бота"),
        types.BotCommand("orders", "Список заказов"),
        types.BotCommand("help", "Помощь"),
        types.BotCommand("status", "Изменить статус заказа"),
        types.BotCommand("stats", "Статистика по заказам")
    ])
    logger.info("Бот запущен")

def start_bot():
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)

if __name__ == "__main__":
    start_bot()


# Добавляем новую функцию для получения URL изображения
async def add_caption_to_image(image_path, caption):
    """Добавляет подпись с белым фоном к изображению"""
    try:
        # Увеличиваем размер шрифта в 2 раза
        font_size = 40  # Было 20
        padding = 20  # Увеличиваем отступы
        line_spacing = 10

        # Укажите правильный путь к шрифту на вашем сервере
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            # Fallback к стандартному шрифту если arial не найден
            font = ImageFont.load_default()

        with Image.open(image_path) as img:
            img_width, img_height = img.size

            # Создаем временное изображение для измерения текста
            temp_draw = ImageDraw.Draw(img)

            # Разбиваем текст на строки с учетом переноса
            lines = []
            for line in caption.split('\n'):
                current_line = []
                for word in line.split():
                    current_line.append(word)
                    test_line = ' '.join(current_line)
                    text_width = temp_draw.textlength(test_line, font=font)
                    if text_width > img_width - 2 * padding:
                        lines.append(' '.join(current_line[:-1]))
                        current_line = [word]
                lines.append(' '.join(current_line))

            # Рассчитываем высоту текстового блока
            text_height = (font_size + line_spacing) * len(lines) + 2 * padding

            # Создаем новое изображение
            new_height = img_height + text_height
            new_img = Image.new("RGB", (img_width, new_height), (255, 255, 255))
            new_img.paste(img, (0, 0))

            draw = ImageDraw.Draw(new_img)

            # Рисуем текст с центральным выравниванием
            y_position = img_height + padding
            for line in lines:
                text_width = draw.textlength(line, font=font)
                x_position = (img_width - text_width) / 2  # Центрирование
                draw.text(
                    (x_position, y_position),
                    line,
                    fill=(0, 0, 0),
                    font=font,
                    stroke_width=1,
                    stroke_fill=(255, 255, 255)
                )
                y_position += font_size + line_spacing

            # Сохранение во временный файл
            fd, temp_path = tempfile.mkstemp(suffix='.jpg')
            new_img.save(temp_path, quality=95)
            os.close(fd)

            return temp_path

    except Exception as e:
        logger.error(f"Ошибка обработки изображения: {str(e)}")
        return image_path

async def get_order_media_items(order):
    try:
        items = await sync_to_async(list)(order.cartitem_set.all())
        media_items = []

        for idx, item in enumerate(items, 1):
            product = await sync_to_async(lambda: item.product)()
            if not product.image:
                continue

            # Получение пути к изображению
            relative_path = await sync_to_async(lambda: product.image.name)()
            absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)
            absolute_path = os.path.normpath(absolute_path)

            # Проверка существования файла
            if not await sync_to_async(os.path.exists)(absolute_path):
                continue

            # Формирование подписи
            total_items = len(items)
            caption = (
                f"Товар {idx}/{total_items}\n"
                f"{product.name}\n"
                f"Количество: {item.quantity} × {product.price}₽"
            )

            # Добавление подписи к изображению
            processed_path = await add_caption_to_image(absolute_path, caption)

            media_items.append({
                'path': processed_path,
                'is_temp': processed_path != absolute_path
            })

        return media_items

    except Exception as e:
        logger.error(f"Ошибка при обработке медиа: {str(e)}")
        return []

# Глобальный экземпляр бота и сессии
bot_instance = Bot(token=settings.TELEGRAM_BOT_TOKEN)

# Синхронный враппер
def sync_send_notification(order):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_telegram_notification(order))
    finally:
        # Корректное закрытие соединений
        loop.run_until_complete(bot_instance.close())
        loop.close()

# Изменения в функции send_telegram_notification
async def send_telegram_notification(order):
    check_telegram_settings()

    try:
        message = await format_order_message(order)

        for chat_id in settings.TELEGRAM_ADMIN_CHAT_IDS:
            media_items = await get_order_media_items(order)
            try:
                # Отправка текста (УБРАН ПАРАМЕТР SESSION)
                for part in split_text(message):
                    await bot_instance.send_message(
                        chat_id=chat_id,
                        text=part,
                        parse_mode="Markdown"
                    )

                # Отправка медиа (УБРАН ПАРАМЕТР SESSION)
                if media_items:
                    for item in media_items:
                        try:
                            with open(item['path'], 'rb') as photo:
                                await bot_instance.send_photo(
                                    chat_id=chat_id,
                                    photo=photo,
                                    parse_mode="Markdown"
                                )
                        finally:
                            if item.get('is_temp', False):
                                await sync_to_async(os.remove)(item['path'])

                logger.info(f"Уведомление отправлено в чат {chat_id}")

            except Exception as e:
                logger.error(f"Ошибка отправки: {str(e)}")
                if media_items:
                    for item in media_items:
                        if item.get('is_temp', False) and await sync_to_async(os.path.exists)(item['path']):
                            await sync_to_async(os.remove)(item['path'])

    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}", exc_info=True)

async def format_order_message(order):
    # Создаем асинхронные версии функций для работы с временем
    async_localtime = sync_to_async(timezone.localtime)
    async_strftime = sync_to_async(lambda dt: dt.strftime('%d.%m.%Y %H:%M'))

    # Получаем и форматируем даты с учетом часового пояса
    order_date = await async_localtime(order.order_date)
    delivery_date = await async_localtime(order.delivery_date)

    items = await sync_to_async(list)(order.cartitem_set.all())

    order_items = []
    for item in items:
        product = await sync_to_async(lambda: item.product)()
        item_total = product.price * item.quantity
        order_items.append(
            f"• *{product.name}*\n"
            f"  {item.quantity} × {product.price} ₽ = {item_total} ₽"
        )

    user = await sync_to_async(lambda: order.user)()
    phone = await sync_to_async(lambda: user.phone if user.phone else "Не указан")()
    address = await sync_to_async(lambda: user.address if user.address else "Не указан")()

    return (
            "🛒 *Новый заказ!*\n\n"
            f"🆔 *#{order.id}*\n"
            f"📅 *Дата заказа:* {await async_strftime(order_date)}\n"
            f"📦 *План доставки:* {await async_strftime(delivery_date)}\n"
            f"💵 *Сумма:* {order.total_price} ₽\n"
            f"👤 *Клиент:* {user.username}\n"
            f"📱 *Телефон:* {phone}\n"
            f"📦 *Адрес доставки:* {order.address}\n\n"
            "*Состав заказа:*\n" + "\n".join(order_items)
    )

def check_telegram_settings():
    required = [
        ('TELEGRAM_BOT_TOKEN', settings.TELEGRAM_BOT_TOKEN),
        ('TELEGRAM_ADMIN_CHAT_IDS', settings.TELEGRAM_ADMIN_CHAT_IDS)
    ]

    for name, value in required:
        if not value:
            raise ImproperlyConfigured(f"Не задана настройка {name}")

    logger.debug(f"Telegram chat IDs: {settings.TELEGRAM_ADMIN_CHAT_IDS}")

# Добавляем обработчик команды /stats через aiogram
@dp.message_handler(commands=['stats'])
async def stats_command(message: types.Message):
    # Асинхронные обертки для работы с ORM
    async_get_stats = sync_to_async(Order.get_stats, thread_sensitive=True)
    async_localtime = sync_to_async(timezone.localtime)
    async_strftime = sync_to_async(lambda dt: dt.strftime('%d.%m.%Y %H:%M'))

    try:
        # Получаем данные асинхронно
        stats = await async_get_stats()
        now = await async_localtime()

        # Форматируем даты
        today_str = await async_strftime(now)
        week_number = now.isocalendar()[1]
        current_year = now.year

        # Словарь русских названий месяцев
        months_ru = [
            'Январь', 'Февраль', 'Март', 'Апрель',
            'Май', 'Июнь', 'Июль', 'Август',
            'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
        ]
        month_name_ru = months_ru[now.month - 1]

        # Формируем ответ
        response = (
            "📊 *Статистика заказов*\n\n"

            f"*Сегодня ({today_str})*\n"
            f"Заказов: {stats['today']['total_orders'] or 0} / "
            f"Сумма: {stats['today']['total_amount'] or 0} ₽\n"
            f"▪ Средний чек: {stats['today']['avg_check'].quantize(Decimal('1.00')) if stats['today']['avg_check'] else 0} ₽\n"
            f"Доставлено всего: {stats['today']['delivered_total']}\n"
            f"Из них вовремя: {stats['today']['delivered_on_time']}\n"
            f"▪ Процент вовремя: {(stats['today']['delivered_on_time'] / stats['today']['delivered_total'] * 100 if stats['today']['delivered_total'] > 0 else 0):.1f}%\n\n"

            f"*Текущая неделя (неделя №{week_number})*\n"
            f"Заказов: {stats['week']['total_orders'] or 0} / "
            f"Сумма: {stats['week']['total_amount'] or 0} ₽\n"
            f"▪ Средний чек: {stats['week']['avg_check'].quantize(Decimal('1.00')) if stats['week']['avg_check'] else 0} ₽\n"
            f"Доставлено всего: {stats['week']['delivered_total']}\n"
            f"Из них вовремя: {stats['week']['delivered_on_time']}\n"
            f"▪ Процент вовремя: {(stats['week']['delivered_on_time'] / stats['week']['delivered_total'] * 100 if stats['week']['delivered_total'] > 0 else 0):.1f}%\n"
            f"Прошлый год: {stats['last_year_week']['total_orders'] or 0} / "
            f"{stats['last_year_week']['total_amount'] or 0} ₽\n\n"

            f"*Текущий месяц ({month_name_ru})*\n"
            f"Заказов: {stats['month']['total_orders'] or 0} / "
            f"Сумма: {stats['month']['total_amount'] or 0} ₽\n"
            f"▪ Средний чек: {stats['month']['avg_check'].quantize(Decimal('1.00')) if stats['month']['avg_check'] else 0} ₽\n"
            f"Доставлено всего: {stats['month']['delivered_total']}\n"
            f"Из них вовремя: {stats['month']['delivered_on_time']}\n"
            f"▪ Процент вовремя: {(stats['month']['delivered_on_time'] / stats['month']['delivered_total'] * 100 if stats['month']['delivered_total'] > 0 else 0):.1f}%\n"
            f"Прошлый год: {stats['last_year_month']['total_orders'] or 0} / "
            f"{stats['last_year_month']['total_amount'] or 0} ₽\n\n"

            f"*Текущий год ({current_year})*\n"
            f"Заказов: {stats['year']['total_orders'] or 0} / "
            f"Сумма: {stats['year']['total_amount'] or 0} ₽\n"
            f"▪ Средний чек: {stats['year']['avg_check'].quantize(Decimal('1.00')) if stats['year']['avg_check'] else 0} ₽\n"
            f"Доставлено всего: {stats['year']['delivered_total']}\n"
            f"Из них вовремя: {stats['year']['delivered_on_time']}\n"
            f"▪ Процент вовремя: {(stats['year']['delivered_on_time'] / stats['year']['delivered_total'] * 100 if stats['year']['delivered_total'] > 0 else 0):.1f}%\n"
            f"Прошлый год: {stats['last_year']['total_orders'] or 0} / "
            f"{stats['last_year']['total_amount'] or 0} ₽"
        )

        await message.answer(response, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Ошибка получения статистики: {str(e)}")
        await message.answer("⚠️ Ошибка при загрузке статистики")

import atexit

@atexit.register
def cleanup():
    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(bot_instance.close())
    except Exception as e:
        logger.error(f"Ошибка при закрытии бота: {str(e)}")