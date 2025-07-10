from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.catalog_view, name='catalog'),
    path('favorites/', views.favorite_products, name='favorites'),
    path('add_to_favorites/<int:product_id>/', views.add_to_favorites, name='add_to_favorites'),
    path('remove_from_favorites/<int:favorite_id>/', views.remove_from_favorites, name='remove_from_favorites'),
    path('<int:product_id>/', views.product_detail, name='product_detail'),
    path('<int:product_id>/reviews/', views.product_reviews, name='product_reviews'),
    path('<int:product_id>/add-review/', views.add_review, name='add_review'),
]