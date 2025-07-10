"""
URL configuration for flower_shop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView  # Импорт для статических шаблонов
from . import views  # Импорт ваших представлений
from users import views as user_views  # Импорт представлений из приложения users
from django.conf import settings
from django.conf.urls.static import static
from .views import home, get_reviews

from .views import main_page

urlpatterns = [
    path('admin/', admin.site.urls),

    # Главная страница (home.html)
    path('', views.home, name='home'),

    # Отдельные маршруты для header и footer (опционально)
    path('header/', TemplateView.as_view(template_name='header.html'), name='header'),
    path('footer/', TemplateView.as_view(template_name='footer.html'), name='footer'),
    path('login/', user_views.login_view, name='login'),  # Маршрут для входа
    #path('cart/', include('orders.urls')),  # Маршрут для корзины (если есть)
    path('orders/', include('orders.urls')),
    path('users/', include('users.urls', namespace='users')),  # Добавьте namespace
    path('catalog/', include('catalog.urls')),
    path('send-callback/', views.send_callback, name='send_callback'), # Маршруты каталога
    path('reviews/', get_reviews, name='get_reviews'),
    path('info/', include('content.urls', namespace='content')),
    path('', main_page, name='main_page'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
