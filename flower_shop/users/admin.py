from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Поля, отображаемые в списке пользователей
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone', 'telegram_id')

    # Поля для фильтрации
    list_filter = ('is_staff', 'is_superuser')

    # Поля для поиска
    search_fields = ('username', 'email', 'phone')

    # Группировка полей в форме редактирования
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name', 'email', 'phone', 'address')}),
        ('Telegram', {'fields': ('telegram_id',)}),
        ('Права', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Даты', {'fields': ('last_login', 'date_joined')}),
    )