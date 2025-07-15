from django.urls import include, path
from djoser.views import TokenCreateView
from rest_framework.routers import DefaultRouter

from .views import (
    AvatarViewSet,
    CurrentUserViewSet,
    FavoriteViewSet,
    IngredientViewSet,
    LogoutView,
    PasswordChangeView,
    RecipesViewSet,
    SubscribeViewSet,
    ShoppingCartViewSet,
    ShortCodeRedirect,
    TagViewSet,
    UserViewSet,
)

v1_router = DefaultRouter()

v1_router.register(r'recipes', ShoppingCartViewSet, basename='shopping_carts')
v1_router.register(r'recipes', FavoriteViewSet, basename='favorite')
v1_router.register('recipes', RecipesViewSet, basename='recipes')
v1_router.register('users', SubscribeViewSet, basename='subscribes')
v1_router.register('users', UserViewSet, basename='users')
v1_router.register('tags', TagViewSet, basename='tags')
v1_router.register('ingredients', IngredientViewSet, basename='ingredients')


urlpatterns = [
    path(
        'users/set_password/',
        PasswordChangeView.as_view(),
        name='set_password'
    ),
    path('users/me/',
         CurrentUserViewSet.as_view({'get': 'retrieve'}), name='me'),
    path('users/me/avatar/', AvatarViewSet.as_view(
        {
            'put': 'update',
            'delete': 'destroy'
        }
    ), name='avatar'),
    path('', include(v1_router.urls)),
    path('auth/token/login/', TokenCreateView.as_view(), name='token-login'),
    path('auth/token/logout/', LogoutView.as_view(), name='token-logout'),
    path('s/<str:short_code>/', ShortCodeRedirect.as_view())
]
