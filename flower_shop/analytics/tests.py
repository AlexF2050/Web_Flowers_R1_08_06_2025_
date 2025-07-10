from django.test import TestCase
from django.core.exceptions import ValidationError
from hypothesis import given, strategies as st, assume
from hypothesis.extra.django import TestCase as HypTestCase
import datetime
from django.apps import apps

Report = apps.get_model('analytics', 'Report')


class ReportTests(TestCase):
    def test_report_creation(self):
        report = Report.objects.create(
            period_start="2024-01-01",
            period_end="2024-01-31",
            total_orders=100,
            total_revenue=500000.00,
            on_time_delivery_percent=95.5
        )
        self.assertAlmostEqual(report.on_time_delivery_percent, 95.5)

    def test_date_validation(self):
        # Создаем объект НЕ через create(), чтобы не сохранять в базу
        report = Report(
            period_start=datetime.date(2024, 2, 1),
            period_end=datetime.date(2024, 1, 1),
            total_orders=0,
            total_revenue=0,
            on_time_delivery_percent=0.0
        )

        with self.assertRaises(ValidationError) as context:
            report.full_clean()  # Явный вызов валидации

        # Проверяем наличие ошибки для period_start
        self.assertIn('period_start', context.exception.message_dict)


class AnalyticsHypothesisTests(HypTestCase):
    @given(
        start_date=st.dates(min_value=datetime.date(2020, 1, 1)),
        end_date=st.dates(min_value=datetime.date(2020, 1, 1)),
        revenue=st.decimals(min_value=0, max_value=10 ** 9)
    )
    def test_report_property_based(self, start_date, end_date, revenue):
        assume(start_date <= end_date)
        report = Report.objects.create(
            period_start=start_date,
            period_end=end_date,
            total_orders=100,
            total_revenue=revenue,
            on_time_delivery_percent=95.0
        )
        self.assertEqual(report.period_start, start_date)
        self.assertEqual(float(report.total_revenue), float(revenue))