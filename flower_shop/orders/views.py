from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from catalog.models import Product
from django.contrib import messages
from .models import Cart, Order, CartItem, OrderItem
from .forms import DeliveryDateForm, DeliveryAddressForm
from .models import Order
import logging
from asgiref.sync import async_to_sync
from bot import send_telegram_notification
from django.db import transaction


@login_required
def checkout_view(request):
    cart = get_object_or_404(Cart, user=request.user)

    if not cart.cartitem_set.exists():
        messages.error(request, "Невозможно оформить пустой заказ")
        return redirect('orders:cart')

    # Проверка наличия товаров
    out_of_stock_items = []
    for item in cart.cartitem_set.all():
        if item.product.quantity < item.quantity:
            out_of_stock_items.append({
                'name': item.product.name,
                'available': item.product.quantity,
                'requested': item.quantity
            })

    if out_of_stock_items:
        error_message = "Невозможно оформить заказ:<br>"
        for item in out_of_stock_items:
            error_message += (
                f"• {item['name']} - доступно {item['available']} шт., "
                f"заказано {item['requested']}<br>"
            )
        error_message += "Корзина была очищена."
        cart.cartitem_set.all().delete()
        messages.error(request, error_message)
        return redirect('orders:cart')

    date_form = DeliveryDateForm(request.POST or None)
    address_form = DeliveryAddressForm(
        user=request.user,
        data=request.POST or None
    )

    if request.method == 'POST':
        if all([date_form.is_valid(), address_form.is_valid()]):
            try:
                use_profile_address = address_form.cleaned_data['use_profile_address']
                address = (
                    request.user.address
                    if use_profile_address
                    else address_form.cleaned_data['address']
                )

                with transaction.atomic():
                    new_order = Order.objects.create(
                        user=request.user,
                        total_price=cart.total_price(),
                        status='ordered',
                        delivery_date=date_form.cleaned_data['delivery_date'],
                        address=address
                    )

                    for cart_item in cart.cartitem_set.all():
                        CartItem.objects.create(
                            order=new_order,
                            product=cart_item.product,
                            quantity=cart_item.quantity
                        )

                    cart.cartitem_set.all().delete()
                    async_to_sync(send_telegram_notification)(new_order)
                    messages.success(request, f"Заказ #{new_order.id} оформлен!")
                    return redirect('orders:my_orders')

            except Exception as e:
                messages.error(request, f"Ошибка: {str(e)}")
                logger.error(f"Ошибка оформления заказа: {str(e)}")
                return redirect('orders:cart')
        else:
            # Логирование ошибок форм
            messages.error(request, "Пожалуйста, исправьте ошибки в форме")
            response = render(request, 'orders_templates/checkout.html', {
                'cart': cart,
                'total': cart.total_price(),
                'date_form': date_form,
                'address_form': address_form
            })

            return response

    return render(request, 'orders_templates/checkout.html', {
        'cart': cart,
        'total': cart.total_price(),
        'date_form': date_form,
        'address_form': address_form
    })

#@login_required
def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return render(request, 'catalog/favorites.html')
    product = get_object_or_404(Product, pk=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('orders:cart')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    return redirect('orders:cart')

def cart_view(request):
    if not request.user.is_authenticated:
        return render(request, 'catalog/favorites.html')
    # Пытаемся получить корзину. Если её нет, вернем пустую.
    cart = Cart.objects.filter(user=request.user).first()
    # Проверяем, есть ли товары в корзине
    if not cart or not cart.products.exists():
        messages.info(request, "Корзина пустая")
    #else: cart = Cart.objects.get(user=request.user)
    return render(request, 'orders_templates/cart.html', {'cart': cart})

#@login_required
def order_history(request):
    if not request.user.is_authenticated:
        return render(request, 'catalog/favorites.html')
    orders = Order.objects.filter(user=request.user) \
        .prefetch_related('cartitem_set__product') \
        .order_by('-order_date')


    return render(request, 'orders_templates/order_history.html', {
        'orders': orders
    })

@login_required
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
                messages.success(request, "Количество обновлено")
            else:
                cart_item.delete()
                messages.success(request, "Товар удален из корзины")
        except ValueError:
            messages.error(request, "Некорректное количество")

    return redirect('orders:cart')

logger = logging.getLogger(__name__)

STATUS_MAPPING = {
    "🆕 Заказано": "ordered",
    "🔧 Собирается": "in_assemble",
    "✅ Собрано": "assembled",
    "🚚 Едет": "in_delivery",
    "📦 Доставлено": "delivered",
    "❌ Отменен": "canceled",
}

@login_required
def add_order_to_cart(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    cart, created = Cart.objects.get_or_create(user=request.user)

    # Переносим товары из заказа в корзину
    for cart_item in order.cartitem_set.all():
        new_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=cart_item.product,
            defaults={'quantity': cart_item.quantity}
        )
        if not created:
            new_item.quantity += cart_item.quantity
            new_item.save()

    messages.success(request, f"Товары из заказа #{order.id} добавлены в корзину!")
    return redirect('orders:cart')