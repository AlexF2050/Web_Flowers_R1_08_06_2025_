import pytest
from hypothesis import given, strategies as st
from hypothesis.extra.django import TestCase  # Изменено
from django.urls import reverse
from django.contrib.admin import site
from django.apps import apps
from django.core.exceptions import ValidationError
from django.test import override_settings

Article = apps.get_model('content', 'Article')

@override_settings(ROOT_URLCONF='flower_shop.flower_shop.urls')
class TestArticleModel(TestCase):  # hypothesis.extra.django.TestCase
    @given(
        title=st.text(max_size=200),
        content=st.text(),
        category=st.sampled_from(['news', 'article', 'promo'])
    )
    def test_article_creation(self, title, content, category):
        article = Article.objects.create(
            title=title,
            content=content,
            category=category
        )
        self.assertEqual(article.title, title)
        self.assertEqual(article.category, category)
        self.assertIsNotNone(article.created_at)
        self.assertEqual(str(article), title)

    def test_category_choices(self):
        choices = dict(Article.CATEGORY_CHOICES)
        expected = {
            'news': 'О компании',
            'article': 'Оплата',
            'promo': 'Доставка'
        }
        self.assertDictEqual(choices, expected)

@override_settings(ROOT_URLCONF='flower_shop.flower_shop.urls')
class TestArticleAdmin(TestCase):
    def test_admin_registration(self):
        self.assertIn(Article, site._registry)

    def test_list_display(self):
        admin_instance = site._registry[Article]
        self.assertEqual(admin_instance.list_display, ('title', 'category', 'created_at'))

    def test_search_fields(self):
        admin_instance = site._registry[Article]
        self.assertEqual(admin_instance.search_fields, ())  # Тест будет ожидать пустой кортеж

@override_settings(ROOT_URLCONF='flower_shop.flower_shop.urls')
class TestContentViews(TestCase):
    def setUp(self):
        self.article_data = {
            'news': Article.objects.create(
                title='About Company',
                content='Company info',
                category='news'
            ),
            'article': Article.objects.create(
                title='Payment Info',
                content='Payment details',
                category='article'
            ),
            'promo': Article.objects.create(
                title='Delivery Info',
                content='Delivery details',
                category='promo'
            )
        }

    def test_payment_view(self):
        response = self.client.get(reverse('content:payment'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            self.article_data['article'].content,
            response.content.decode()
        )

    def test_delivery_view(self):
        response = self.client.get(reverse('content:delivery'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'content/delivery_info.html',
            [t.name for t in response.templates]
        )

    def test_about_view_context(self):
        response = self.client.get(reverse('content:about'))
        self.assertEqual(response.context['article'].category, 'news')

    def test_404_on_missing_article(self):
        Article.objects.all().delete()
        response = self.client.get(reverse('content:payment'))
        self.assertEqual(response.status_code, 404)

@override_settings(ROOT_URLCONF='flower_shop.flower_shop.urls')
class TestContentManagement(TestCase):
    def test_article_creation(self):
        article = Article.objects.create(
            title="Test Article",
            content="Sample content",
            category="news"
        )
        self.assertEqual(article.category, "news")

    def test_article_display(self):
        Article.objects.create(
            title="Visible Article",
            content="Content",
            category="news"  # Категория должна совпадать с фильтром во view
        )
        response = self.client.get(reverse('content:about'))
        self.assertContains(response, "Content")  # Используем assertContains

@override_settings(ROOT_URLCONF='flower_shop.flower_shop.urls')
class TestContentValidation(TestCase):
    def test_invalid_category(self):
        with self.assertRaises(ValidationError):
            article = Article(
                title="Invalid Category",
                content="Content",
                category="invalid"
            )
            article.full_clean()