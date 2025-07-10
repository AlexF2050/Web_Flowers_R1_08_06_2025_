import django_filters
from django import forms
from .models import Product, ProductColor

class ProductFilter(django_filters.FilterSet):

    group = django_filters.ChoiceFilter(
        choices=Product.GROUP_CHOICES,
        label='Группа',
        empty_label="Все группы"
    )

    subgroup = django_filters.ChoiceFilter(
        choices=Product.SUBGROUP_CHOICES,
        label='Подгруппа',
        empty_label="Все подгруппы"
    )

    flower_type = django_filters.ChoiceFilter(
        choices=Product.FLOWER_TYPE_CHOICES,
        label='Тип цветка',
        empty_label="Все типы"
    )

    colors = django_filters.ModelMultipleChoiceFilter(
        field_name='colors__name',
        queryset=ProductColor.objects.all(),
        label='Цвета',
        widget=forms.CheckboxSelectMultiple,
        method='filter_colors'
    )

    is_new = django_filters.BooleanFilter(
        field_name='is_new',
        widget=forms.CheckboxInput,
        label="Новинки",
        method='filter_new'
    )

    is_bestseller = django_filters.BooleanFilter(
        field_name='is_bestseller',
        widget=forms.CheckboxInput,
        label="Хиты продаж",
        method='filter_bestseller'
    )
    ordering = django_filters.OrderingFilter(
        fields=(
            ('price', 'price'),
            ('-price', '-price'),
        ),
        field_labels={
            'price': 'По возрастанию цены',
            '-price': 'По убыванию цены',
        },
        label='Сортировка',
        empty_label='По умолчанию'
    )


    def filter_colors(self, queryset, name, value):
        return queryset.filter(colors__name__in=value).distinct() if value else queryset

    def filter_new(self, queryset, name, value):
        return queryset.filter(is_new=True) if value else queryset

    def filter_bestseller(self, queryset, name, value):
        return queryset.filter(is_bestseller=True) if value else queryset

    class Meta:
        model = Product
        fields = ['group', 'subgroup', 'flower_type', 'colors', 'is_new', 'is_bestseller']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Явно сбрасываем начальные значения для checkbox
        self.form.fields['is_new'].initial = False
        self.form.fields['is_bestseller'].initial = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Убедитесь, что фильтры не имеют значений по умолчанию
        self.form.initial = {}