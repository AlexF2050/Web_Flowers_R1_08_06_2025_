from django.urls import path
from . import views

app_name = 'content'

urlpatterns = [
    path('payment/', views.payment_info, name='payment'),
    path('delivery/', views.delivery_info, name='delivery'),
    path('about/', views.about_company, name='about'),
]