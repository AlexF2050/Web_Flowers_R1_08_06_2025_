from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Case, When, F, Count, Sum, IntegerField
from datetime import datetime, timedelta

class OrderManager(models.Manager):
    def get_period_stats(self, start_date, end_date):
        stats = self.filter(
            order_date__gte=start_date,
            order_date__lte=end_date
        ).exclude(status="canceled").aggregate(
            total_orders=Count('id'),
            total_amount=Sum('total_price'),
            delivered_total=Count(
                Case(
                    When(status='delivered', then=1),
                    output_field=IntegerField()
                )
            ),
            delivered_on_time=Count(
                Case(
                    When(
                        status='delivered',
                        delivered_date__lte=F('delivery_date'),
                        then=1
                    ),
                    output_field=IntegerField()
                )
            )
        )

        # Расчет среднего чека
        if stats['total_orders'] > 0 and stats['total_amount']:
            stats['avg_check'] = stats['total_amount'] / stats['total_orders']
        else:
            stats['avg_check'] = 0

        return stats

class Order(models.Model):
    STATUS_CHOICES = [
        ("ordered", "Заказано"),
        ("in_assemble", "Собирается"),
        ("assembled", "Собрано"),
        ("in_delivery", "Едет"),
        ("delivered", "Доставлено"),
        ("canceled", "Отменено"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Пользователь"
    )
    products = models.ManyToManyField(
        'catalog.Product',
        through='OrderItem',  # Добавляем промежуточную модель
        verbose_name="Товары"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ordered",
        verbose_name="Статус"
    )
    order_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата заказа"
    )
    delivery_date = models.DateTimeField(
        verbose_name="Дата доставки",
        null=True,
        blank=True
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Общая сумма",
        default=0
    )
    ordered_date = models.DateTimeField(null=True, blank=True)
    in_assemble_date = models.DateTimeField(null=True, blank=True)
    assembled_date = models.DateTimeField(null=True, blank=True)
    in_delivery_date = models.DateTimeField(null=True, blank=True)
    delivered_date = models.DateTimeField(null=True, blank=True)
    canceled_date = models.DateTimeField(null=True, blank=True)
    address = models.CharField(max_length=255, verbose_name="Адрес доставки")

    class Meta:
        app_label = 'orders'  # Явное указание app_lab

    def save(self, *args, **kwargs):
        status_date_map = {
            'ordered': 'ordered_date',
            'in_assemble': 'in_assemble_date',
            'assembled': 'assembled_date',
            'in_delivery': 'in_delivery_date',
            'delivered': 'delivered_date',
            'canceled': 'canceled_date',
        }
        if self.status in status_date_map:
            date_field = status_date_map[self.status]
            if not getattr(self, date_field):
                setattr(self, date_field, timezone.now())
        super().save(*args, **kwargs)

    objects = OrderManager()

    @classmethod
    def get_stats(cls):
        now = timezone.localtime()
        today = now.date()
        tz = timezone.get_current_timezone()

        # Текущая неделя (с понедельника)
        start_week = today - timedelta(days=today.weekday())
        start_week = timezone.make_aware(
            datetime.combine(start_week, datetime.min.time()),
            tz
        )
        end_week = start_week + timedelta(days=6, hours=23, minutes=59, seconds=59)

        # Текущий месяц
        start_month = timezone.make_aware(
            datetime(today.year, today.month, 1),
            tz
        )
        next_month = start_month + timedelta(days=32)
        end_month = next_month.replace(day=1) - timedelta(seconds=1)

        # Текущий год
        start_year = timezone.make_aware(
            datetime(today.year, 1, 1),
            tz
        )
        end_year = timezone.make_aware(
            datetime(today.year, 12, 31, 23, 59, 59),
            tz
        )

        # Прошлый год
        last_year = today.year - 1

        # Периоды для сравнения с прошлым годом
        last_year_week_start = timezone.make_aware(
            datetime(last_year, start_week.month, start_week.day),
            tz
        )
        last_year_week_end = timezone.make_aware(
            datetime(last_year, end_week.month, end_week.day, 23, 59, 59),
            tz
        )

        last_year_month_start = timezone.make_aware(
            datetime(last_year, start_month.month, 1),
            tz
        )
        last_year_month_end = last_year_month_start + timedelta(days=32)
        last_year_month_end = last_year_month_end.replace(day=1) - timedelta(seconds=1)

        last_year_start = timezone.make_aware(
            datetime(last_year, 1, 1),
            tz
        )
        last_year_end = timezone.make_aware(
            datetime(last_year, 12, 31, 23, 59, 59),
            tz
        )

        return {
            'today': cls.objects.get_period_stats(
                now.replace(hour=0, minute=0, second=0, microsecond=0),
                now.replace(hour=23, minute=59, second=59, microsecond=999999)
            ),
            'week': cls.objects.get_period_stats(start_week, end_week),
            'month': cls.objects.get_period_stats(start_month, end_month),
            'year': cls.objects.get_period_stats(start_year, end_year),
            'last_year_week': cls.objects.get_period_stats(
                last_year_week_start,
                last_year_week_end
            ),
            'last_year_month': cls.objects.get_period_stats(
                last_year_month_start,
                last_year_month_end
            ),
            'last_year': cls.objects.get_period_stats(
                last_year_start,
                last_year_end
            )
        }

    def __str__(self):
        return f"Заказ #{self.id}"

class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Пользователь"
    )
    products = models.ManyToManyField(
        'catalog.Product',
        through='CartItem',
        verbose_name="Товары"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    def total_price(self):
        return sum(item.product.price * item.quantity for item in self.cartitem_set.all())

    def total_items(self):
        return sum(item.quantity for item in self.cartitem_set.all())

    def __str__(self):
        return f"Корзина {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Корзина"
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Заказ",
        related_name='cartitem_set'  # Добавляем related_name

    )
    product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(cart__isnull=False, order__isnull=True) |
                    models.Q(cart__isnull=True, order__isnull=False)
                ),
                name="only_one_relation"
            )
        ]

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

class DeliveryCity(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название города")
    is_available = models.BooleanField(
        verbose_name="Доступен для доставки",
        default=True
    )

    def __str__(self):
        return self.name


class OrderItem(models.Model):
    cart = models.ForeignKey(
        Order,  # Убедитесь, что это ForeignKey на модель Order
        on_delete=models.CASCADE,
        verbose_name="Заказ"  # Добавьте verbose_name для ясности
    )
    product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} x{self.quantity} (Order #{self.cart.id})"  # Используем self.cart.id