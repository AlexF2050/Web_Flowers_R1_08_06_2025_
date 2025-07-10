from django.core.exceptions import ValidationError
from django.db import models

class Report(models.Model):
    period_start = models.DateField(verbose_name="Начало периода")
    period_end = models.DateField(verbose_name="Конец периода")
    total_orders = models.IntegerField(verbose_name="Количество заказов", default=0)
    total_revenue = models.DecimalField(
        verbose_name="Общая выручка",
        max_digits=12,
        decimal_places=2,
        default=0
    )
    on_time_delivery_percent = models.FloatField(verbose_name="% доставки в срок")
    created_at = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True)

    def clean(self):
        if self.period_start > self.period_end:
            raise ValidationError({
                'period_start': 'Дата начала не может быть позже даты окончания!'
            })
        super().clean()

    def __str__(self):
        return f"Отчет за {self.period_start} - {self.period_end}"