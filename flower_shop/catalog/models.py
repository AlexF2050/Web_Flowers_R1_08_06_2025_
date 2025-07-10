from django.db import models
from django.conf import settings

# class Color(models.Model):
#     name = models.CharField(max_length=50, unique=True, verbose_name="Цвет")
#
#     def __str__(self):
#         return self.name

class ProductColor(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Цвет")
    css_name = models.CharField(max_length=50, blank=True, verbose_name="CSS-класс")

    class Meta:
        #app_label = 'catalog'  # Добавил для теста явное указание приложения
        verbose_name = "Цвет"
        verbose_name_plural = "Цвета"

    def __str__(self):
        return self.name

class Product(models.Model):
    GROUP_CHOICES = [
        ('Одиночные цветы', 'Одиночные цветы'),
        ('Букеты', 'Букеты'),
    ]
    SUBGROUP_CHOICES = [
        ('Розы', 'Розы'),
        ('Хризантемы', 'Хризантемы'),
    ]
    FLOWER_TYPE_CHOICES = [
        # Для роз
        ('Красные розы', 'Красные розы'),
        ('Белые розы', 'Белые розы'),

        # Новые типы для Хризантемы
        ('Простые хризантемы', ' Простые хризантемы'),
        ('Декоративные хризантемы', 'Декоративные хризантемы'),

        # Дополнительные варианты
        ('Анемоновидные хризантемы', 'Анемоновидные хризантемы'),
        ('Изогнутые хризантемы', 'Изогнутые хризантемы'),
    ]

    group = models.CharField(max_length=100, choices=GROUP_CHOICES, default='Одиночные цветы', verbose_name="Группа")
    subgroup = models.CharField(max_length=100, choices=SUBGROUP_CHOICES, default='Розы', verbose_name="Подгруппа")
    flower_type = models.CharField(max_length=100, choices=FLOWER_TYPE_CHOICES, default='Красные розы', verbose_name="Тип цветка")
    name = models.CharField(max_length=200, verbose_name="Название")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")

    image = models.ImageField(
        upload_to="products/",
        verbose_name="Изображение",
        null=True,  # Разрешить NULL в базе данных
        blank=True  # Разрешить пустое значение в формах
    )
    colors = models.ManyToManyField(ProductColor, verbose_name="Основные цвета")
    is_new = models.BooleanField(default=False, verbose_name="Новинка")
    is_bestseller = models.BooleanField(default=False, verbose_name="Хит продаж")
    created_at = models.DateTimeField(auto_now_add=True)

    quantity = models.PositiveIntegerField(
        verbose_name="Количество на складе",
        default=1)

    #class Meta:
        #app_label = 'catalog'  # Добавил для теста явное указание приложения

    def __str__(self):
        return self.name

class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Используем кастомную модель пользователя
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        #app_label = 'catalog'  # Добавил для теста явное указание приложения

    def __str__(self):
        return f"{self.user} - {self.product.name}"

class Review(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Пользователь"
    )
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        verbose_name="Товар"
    )
    text = models.TextField(verbose_name="Текст отзыва")
    rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        verbose_name="Оценка"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,  # Убираем default, добавляем auto_now_add
        verbose_name="Дата создания"
    )

    #class Meta:
        #app_label = 'catalog'  # Добавил для теста явное указание приложения

    def __str__(self):
        return f"Отзыв от {self.user.username}"