from django.contrib import admin
from .models import Product, Review, ProductColor, Favorite
#from .models import Article

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'group',
        'subgroup',
        'flower_type',
        'price',
        'is_new',
        'is_bestseller',
        'quantity'
    )
    list_editable = (
        'price',
        'is_new',
        'is_bestseller',
        'quantity'
    )
    list_filter = ('group', 'subgroup', 'flower_type')
    filter_horizontal = ('colors',)


@admin.register(ProductColor)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'css_name')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'product__name', 'text')

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')

# @admin.register(Article)
# class ArticleAdmin(admin.ModelAdmin):
#     list_display = ('title', 'category', 'created_at')
#     search_fields = ('title', 'content')