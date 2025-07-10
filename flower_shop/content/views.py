from django.shortcuts import render, get_object_or_404
from .models import Article

def payment_info(request):
    article = get_object_or_404(Article, category='article')
    return render(request, 'content/payment_info.html', {'article': article})

def delivery_info(request):
    article = get_object_or_404(Article, category='promo')
    return render(request, 'content/delivery_info.html', {'article': article})

def about_company(request):
    article = get_object_or_404(Article, category='news')
    return render(request, 'content/about_company.html', {'article': article})