from django.contrib import admin
from .models import Order, Cart, CartItem, DeliveryCity

class CartInline(admin.TabularInline):
    model = CartItem
    extra = 1
    fields = ('product', 'quantity')
    raw_id_fields = ('product',)
    fk_name = 'cart'  # Явно указываем связь с корзиной

class OrderInline(admin.TabularInline):
    model = CartItem
    extra = 1
    fields = ('product', 'quantity')
    raw_id_fields = ('product',)
    fk_name = 'order'  # Явно указываем связь с заказом

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'status',
        'order_date',
        'delivery_date',
        'total_price',
        'assembled_date',
        'canceled_date',
        'delivered_date',
        'in_assemble_date',
        'in_delivery_date',
        'ordered_date',
    )
    list_filter = ('status', 'ordered_date')
    search_fields = ('user__username', 'id')
    inlines = [OrderInline]  # Используем модифицированный инлайн
    readonly_fields = ('order_date',)
    #actions = ['delete_orders']

    def total_price(self, obj):
        # Теперь считаем через CartItem, связанный с заказом
        return sum(
            item.product.price * item.quantity
            for item in obj.cartitem_set.filter(order=obj)
        )
    total_price.short_description = "Сумма заказа"

    def delete_orders(self, request, queryset):
        for order in queryset:
            order.delete()
        self.message_user(request, "Выбранные заказы были успешно удалены.")

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'total_price', 'total_items')
    inlines = [CartInline]
    raw_id_fields = ('user',)

@admin.register(DeliveryCity)
class DeliveryCityAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_available')
    list_editable = ('is_available',)
    search_fields = ('name',)