from django.urls import path
from .import views

app_name = 'orders'  # Опционально: пространство имен

urlpatterns = [
    # Маршрут для корзины
    path('cart/', views.cart_view, name='cart'),

    # Маршрут для оформления заказа
    path('checkout/', views.checkout_view, name='checkout'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),

    # Маршрут для истории заказов
    path('my-orders/', views.order_history, name='my_orders'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/add-order/<int:order_id>/', views.add_order_to_cart, name='add_order_to_cart'),

]