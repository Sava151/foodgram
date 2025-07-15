from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import Favorite, Follow, ShoppingCart, User
from .models import Ingredient, Recipes, RecipeIngredient, Tag


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name')
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_superuser', 'is_active')


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipes)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author',)
    search_fields = ('name', 'author__username')
    list_filter = ('tags',)
    inlines = [RecipeIngredientInline]
    readonly_fields = ('favorite_count',)

    @admin.display(description='Количество добавлений в избранное')
    def favorite_count(self, obj):
        return Favorite.objects.filter(recipe=obj).count()


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
