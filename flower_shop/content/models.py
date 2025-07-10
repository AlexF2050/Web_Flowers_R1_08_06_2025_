from django.db import models

class Article(models.Model):
    CATEGORY_CHOICES = [
        ('news', 'О компании'),
        ('article', 'Оплата'),
        ('promo', 'Доставка'),
    ]

    title = models.CharField(
        max_length=200,
        verbose_name="Заголовок"
    )
    content = models.TextField(verbose_name="Содержание",
        help_text="Используйте HTML-теги для форматирования" )
    created_at = models.DateTimeField(
        verbose_name="Дата создания",
        auto_now_add=True
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        verbose_name="Категория"
    )

    def __str__(self):
        return self.title