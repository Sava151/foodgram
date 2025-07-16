from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Count

from users.models import Favorite, Follow, ShoppingCart
from .models import Ingredient, Recipes, RecipeIngredient, Tag

User = get_user_model()


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1


@admin.register(Recipes)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorite_count',)
    search_fields = ('name', 'author__username')
    list_filter = ('tags',)
    inlines = [RecipeIngredientInline]
    readonly_fields = ('favorite_count',)

    @admin.display(description='Количество добавлений в избранное')
    def favorite_count(self, obj):
        return obj.favorite_count

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(favorite_count=Count('favorited_by'))
        return queryset


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'following')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
