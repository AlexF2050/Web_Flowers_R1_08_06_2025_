from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import requests
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Count
from django.db.models import Avg
from catalog.models import Review
from django.shortcuts import render
from catalog.models import Product  # Импортируйте вашу модель продукта


def header(request):
    return render(request, 'header.html')

def footer(request):
    return render(request, 'footer.html')

@csrf_exempt
@require_POST
def send_callback(request):
    try:
        # Получаем данные из формы
        phone = request.POST.get('phone', '').strip()
        city = request.POST.get('city', 'Не указан').strip()

        # Валидация номера телефона
        if not phone:
            return JsonResponse({'status': 'error', 'message': 'Не указан номер телефона'}, status=400)

        # Проверка настроек Telegram
        if not all([settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_ADMIN_CHAT_ID]):
            raise ValueError("Не настроены параметры Telegram")

        # Формируем сообщение
        message = (
            "🔔 Новый запрос на обратный звонок!\n"
            f"📞 Телефон: {phone}\n"
            f"🏙 Город: {city}\n"
        )

        # Отправка в Telegram
        response = requests.post(
            f'https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage',
            json={
                'chat_id': settings.TELEGRAM_ADMIN_CHAT_ID,
                'text': message,
                'parse_mode': 'Markdown'
            },
            timeout=5
        )

        response.raise_for_status()
        return JsonResponse({'status': 'ok'})

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка Telegram API: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Ошибка связи с сервером Telegram'
        }, status=500)

    except Exception as e:
        logger.error(f"Общая ошибка: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': 'Внутренняя ошибка сервера'
        }, status=500)

def home(request):
    # Получаем новинки (продукты с is_new=True)
    new_products = Product.objects.filter(is_new=True)

    # Основная статистика
    reviews_stats = Review.objects.aggregate(
        avg_rating=Avg('rating'),
        total=Count('id')
    )

    context = {
        'new_products': new_products,
        'average_rating': round(reviews_stats['avg_rating'] or 0, 1),
        'reviews_count': reviews_stats['total']
    }
    return render(request, 'home.html', context)


def get_reviews(request):
    # Получаем все отзывы с оптимизацией запросов
    reviews = Review.objects.select_related('user', 'product').all().order_by('-created_at')

    # Сериализуем данные
    reviews_data = []
    for review in reviews:
        reviews_data.append({
            'user': review.user.username,
            'product': review.product.name,
            'text': review.text,
            'rating': review.rating,
            'date': review.created_at.strftime("%d.%m.%Y %H:%M")
        })

    return JsonResponse({'reviews': reviews_data})

def main_page(request):
    # Получаем новинки (продукты с is_new=True)
    new_products = Product.objects.filter(is_new=True)

    # Передаем в контекст шаблона
    context = {
        'new_products': new_products,
        # Другие переменные контекста...
        'average_rating': 4.5  # Пример, замените на реальные данные
    }
    return render(request, 'home.html', context)