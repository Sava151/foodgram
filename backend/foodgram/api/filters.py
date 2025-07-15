from django_filters import FilterSet, ModelMultipleChoiceFilter, NumberFilter

from recipes.models import Recipes, Tag
from users.models import Favorite, ShoppingCart


class RecipeFilter(FilterSet):
    is_in_shopping_cart = NumberFilter(
        method='filter_in_shopping_cart'
    )
    is_favorited = NumberFilter(
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
        if not user.is_authenticated:
            return Recipes.objects.none()
        favorites_ids = Favorite.objects.filter(
            user=user
        ).values_list('recipe_id', flat=True)
        if value == 1:
            return queryset.filter(id__in=favorites_ids)
        elif value == 0:
            return queryset.exclude(id__in=favorites_ids)

    def filter_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return Recipes.objects.none()
        cart_recipe_ids = ShoppingCart.objects.filter(
            user=user
        ).values_list('recipe_id', flat=True)
        if value == 1:
            return queryset.filter(id__in=cart_recipe_ids)
        elif value == 0:
            return queryset.exclude(id__in=cart_recipe_ids)
        return queryset
