from django_filters.rest_framework import (
    BooleanFilter,
    CharFilter,
    FilterSet,
    ModelMultipleChoiceFilter,
)

from recipes.models import Ingredient, Recipes, Tag


class IngredientFilter(FilterSet):
    name = CharFilter(lookup_expr='icontains')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    is_in_shopping_cart = BooleanFilter(
        method='filter_in_shopping_cart'
    )
    is_favorited = BooleanFilter(
        method='filter_is_favorited'
    )
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )

    class Meta:
        model = Recipes
        fields = (
            'author',
        )

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated or value is None:
            return queryset
        if value:
            return queryset.filter(favorited_by__user=user)
        else:
            return queryset.exclude(favorited_by__user=user)

    def filter_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated or value is None:
            return queryset
        if value:
            return queryset.filter(in_shopping_carts__user=user)
        else:
            return queryset.exclude(in_shopping_carts__user=user)
