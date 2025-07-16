from django.urls import include, path
from djoser.views import TokenCreateView, TokenDestroyView
from rest_framework.routers import DefaultRouter

from .views import (
    IngredientViewSet,
    RecipesViewSet,
    TagViewSet,
    UserViewSet,
)

v1_router = DefaultRouter()

v1_router.register('users', UserViewSet, basename='users')
v1_router.register('recipes', RecipesViewSet, basename='recipes')
v1_router.register('tags', TagViewSet, basename='tags')
v1_router.register('ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('', include(v1_router.urls)),
    path('auth/token/login/', TokenCreateView.as_view(), name='token-login'),
    path(
        'auth/token/logout/',
        TokenDestroyView.as_view(),
        name='token-logout'
    ),
]
