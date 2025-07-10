from django.test import TestCase, override_settings
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from hypothesis import given, strategies as st
from hypothesis.extra.django import TestCase as HypTestCase, from_model
from django.apps import apps

# Получаем модели через apps.get_model()
Product = apps.get_model('catalog', 'Product')
ProductColor = apps.get_model('catalog', 'ProductColor')
Review = apps.get_model('catalog', 'Review')
CustomUser = apps.get_model('users', 'CustomUser')

# Фиксируем правильный ROOT_URLCONF для всех тестов
@override_settings(ROOT_URLCONF='flower_shop.flower_shop.urls')
class ProductModelTests(TestCase):
    def setUp(self):
        self.color = ProductColor.objects.create(name="Red", css_name="#ff0000")
        self.product = Product.objects.create(
            name="Test Product",
            price=1000.00,
            group="Букеты",
            subgroup="Розы"
        )
        self.product.colors.add(self.color)

    def test_product_str_representation(self):
        self.assertEqual(str(self.product), "Test Product")

    def test_product_default_values(self):
        self.assertFalse(self.product.is_new)
        self.assertFalse(self.product.is_bestseller)
        self.assertEqual(self.product.quantity, 1)

@override_settings(ROOT_URLCONF='flower_shop.flower_shop.urls')
class CatalogViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        test_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'',
            content_type='image/jpeg'
        )
        cls.user = CustomUser.objects.create_user(username="testuser", password="testpass123")
        cls.product = Product.objects.create(
            name="Test Item",
            price=500.00,
            image=test_image
        )

    def test_catalog_view_status_code(self):
        response = self.client.get(reverse('catalog:catalog'))
        self.assertEqual(response.status_code, 200)

    def test_product_search_functionality(self):
        response = self.client.get(reverse('catalog:catalog') + '?q=Test')
        self.assertContains(response, "Test Item")

@override_settings(ROOT_URLCONF='flower_shop.urls')
class ReviewTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username="reviewuser", password="testpass")
        self.product = Product.objects.create(name="Review Product", price=750.00)

    def test_valid_review_creation(self):
        review = Review.objects.create(
            user=self.user,
            product=self.product,
            text="Great product!",
            rating=5
        )
        self.assertEqual(review.rating, 5)

    def test_invalid_rating_validation(self):
        with self.assertRaises(ValidationError):
            Review.objects.create(
                user=self.user,
                product=self.product,
                text="Bad rating",
                rating=6
            ).full_clean()

@override_settings(ROOT_URLCONF='flower_shop.flower_shop.urls')
class CatalogHypothesisTests(HypTestCase):
    @given(
        instance=from_model(
            Review,
            product=from_model(Product),
            user=from_model(CustomUser),
            rating=st.integers(min_value=1, max_value=5),
            text=st.text(min_size=1)
        )
    )
    def test_review_validation_properties(self, instance):
        try:
            instance.full_clean()
        except ValidationError as e:
            if 'rating' in e.message_dict:
                self.fail(f"Unexpected validation error for rating: {e}")

@override_settings(ROOT_URLCONF='flower_shop.flower_shop.urls')
class ProductFilterTests(TestCase):
    def test_multiple_color_filtering(self):
        test_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'',
            content_type='image/jpeg'
        )
        color1 = ProductColor.objects.create(name="Blue", css_name="#0000ff")
        color2 = ProductColor.objects.create(name="Green", css_name="#00ff00")
        product = Product.objects.create(
            name="Multicolor Product",
            price=2000,
            image=test_image
        )
        product.colors.add(color1, color2)

        response = self.client.get(
            reverse('catalog:catalog') + f"?colors={color1.id}&colors={color2.id}"
        )
        self.assertContains(response, "Multicolor Product")