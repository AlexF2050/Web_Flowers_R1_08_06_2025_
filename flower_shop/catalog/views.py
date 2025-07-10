from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Favorite
from .filters import ProductFilter
import re
from django.contrib import messages

from django.db.models import Avg
from .models import Product, Review
from .forms import ReviewForm

# views.py
def catalog_view(request):
    # Исходный набор всех товаров
    queryset = Product.objects.all()

    # Применяем поиск
    search_query = request.GET.get('q', '').strip()
    if search_query:

        if '*' in search_query:
            # Режим wildcard с регулярными выражениями
            regex_pattern = search_query.replace('*', '.*')
            regex_pattern = re.escape(regex_pattern).replace(r'\.\*', '.*')
            queryset = queryset.filter(name__iregex=f'^{regex_pattern}$')
        else:
            # Обычный регистронезависимый поиск
            queryset = queryset.filter(name__icontains=search_query)

    # Создаем фильтр без начальных значений
    product_filter = ProductFilter(
        request.GET if request.GET else None,  # Важно для первого открытия
        queryset=queryset
    )

    # Применяем фильтрацию и сортировку
    filtered_products = product_filter.qs

    # Дополнительный фильтр "В наличии"
    if request.GET.get('in_stock') == 'on':
        filtered_products = filtered_products.filter(quantity__gt=0)

    # Проверка активных фильтров
    has_filters = any(
        value for key, value in request.GET.items()
        if key not in ['q', 'page'] and value
    )

    return render(request, 'catalog/catalog.html', {
        'filter': product_filter,
        'products': filtered_products,
        'search_query': search_query,
        'has_filters': has_filters,
    })

def favorite_products(request):
    if not request.user.is_authenticated:
        return render(request, 'catalog/favorites.html')
    favorites = Favorite.objects.filter(user=request.user).select_related('product')
    return render(request, 'catalog/favorites.html', {'favorites': favorites})

@login_required
def add_to_favorites(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            product=product
        )

        if not created:
            favorite.delete()
            messages.success(request, "Товар удалён из избранного")
        else:
            messages.success(request, "Товар добавлен в избранное")

    return redirect(request.META.get('HTTP_REFERER', 'catalog'))

@login_required
def remove_from_favorites(request, favorite_id):
    favorite = get_object_or_404(Favorite, id=favorite_id, user=request.user)
    favorite.delete()
    return redirect('catalog:favorites')

def product_detail(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    reviews = Review.objects.filter(product=product)
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    user_has_review = False

    if request.user.is_authenticated:
        user_has_review = Review.objects.filter(
            user=request.user,
            product=product
        ).exists()

    return render(request, 'catalog/product_detail.html', {
        'product': product,
        'average_rating': round(avg_rating, 1),
        'reviews_count': reviews.count(),
        'user_has_review': user_has_review
    })

@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    if Review.objects.filter(user=request.user, product=product).exists():
        return redirect('catalog:product_detail', product_id=product_id)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product
            review.save()
            return redirect('catalog:product_detail', product_id=product_id)
    else:
        form = ReviewForm()

    return render(request, 'catalog/add_review.html', {
        'form': form,
        'product': product
    })

def product_reviews(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    reviews = Review.objects.filter(product=product).select_related('user')
    return render(request, 'catalog/reviews_list.html', {
        'product': product,
        'reviews': reviews
    })