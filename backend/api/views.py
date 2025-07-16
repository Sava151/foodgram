from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from djoser.serializers import UserCreateSerializer, SetPasswordSerializer
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    SAFE_METHODS
)
from rest_framework.response import Response

from recipes.models import (
    Ingredient,
    Tag,
    Recipes,
    RecipeIngredient
)
from users.models import Favorite, Follow, ShoppingCart
from .filters import IngredientFilter, RecipeFilter
from .permission import AuthorOrReadOnly
from .pagination import LimitPagination, LimitOffsetPaginationWithDefault
from .serializers import (
    AvatarSerializer,
    IngredientSerializer,
    RecipesListDetailSerializer,
    RecipeCreateUpdateSerializer,
    RecipeShortSerializer,
    TagSerializer,
    UserSerializer,
    UserSubscribeSerializer
)

User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = LimitPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action == 'set_password':
            return SetPasswordSerializer
        return UserSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            {
                'request': self.request,
            }
        )
        return context

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar'
    )
    def avata_actions(self, request):
        user = request.user
        if request.method == 'PUT':
            if user.avatar:
                user.avatar.delete(save=False)
            serializer = AvatarSerializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        else:
            if user.avatar:
                user.avatar.delete(save=False)
                user.avatar = None
                user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        author = get_object_or_404(User, pk=id)
        print(author)
        user = request.user

        if request.method == 'POST':
            return self.subscribe_user(user, author)
        elif request.method == 'DELETE':
            return self.unsubscribe_user(user, author)

    def subscribe_user(self, user, author):
        if user == author:
            return Response(
                {'error': 'Нельзя подписаться на себя'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if Follow.objects.filter(user=user, following=author).exists():
            return Response(
                {'error': 'Подписка уже существует'},
                status=status.HTTP_400_BAD_REQUEST
            )

        Follow.objects.create(user=user, following=author)

        recipes_limit = self.request.query_params.get('recipes_limit')
        serializer = UserSubscribeSerializer(
            author,
            context={
                'request': self.request,
                'recipes_limit': recipes_limit
            }
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def unsubscribe_user(self, user, author):
        follow = Follow.objects.filter(user=user, following=author).first()
        if not follow:
            return Response(
                {'error': 'Подписка не найдена'},
                status=status.HTTP_400_BAD_REQUEST
            )

        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        user = request.user
        authors = User.objects.filter(following__user=user)

        recipes_limit = request.query_params.get('recipes_limit')
        paginator = LimitPagination()
        page = paginator.paginate_queryset(authors, request)

        context = {
            'request': request,
            'recipes_limit': recipes_limit
        }

        if page is not None:
            serializer = UserSubscribeSerializer(
                page,
                many=True,
                context=context
            )
            return paginator.get_paginated_response(serializer.data)

        serializer = UserSubscribeSerializer(
            authors,
            many=True,
            context=context
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class RecipesViewSet(viewsets.ModelViewSet):
    permission_classes = (AuthorOrReadOnly,)
    pagination_class = LimitOffsetPaginationWithDefault
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipesListDetailSerializer
        return RecipeCreateUpdateSerializer

    def get_queryset(self):
        queryset = Recipes.objects.select_related(
            'author'
        ).prefetch_related(
            'tags',
            'recipe_ingredients__ingredient'
        ).all()
        return queryset

    def _add_relation(self, request, pk, relation_model, error_message):
        recipe = get_object_or_404(Recipes, pk=pk)
        relation, created = relation_model.objects.get_or_create(
            user=request.user,
            recipe=recipe
        )
        if not created:
            return Response(
                {'detail': error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = RecipeShortSerializer(
            recipe,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _delete_relation(self, request, pk, relation_model, error_message):
        recipe = get_object_or_404(Recipes, pk=pk)
        deleted = relation_model.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()
        if deleted[0] == 0:
            return Response(
                {'detail': error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            return self._add_relation(
                request,
                pk,
                Favorite,
                'Рецепт уже в избранном'
            )
        return self._delete_relation(
            request,
            pk,
            Favorite,
            'Рецепт отсутствует в избранном'
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            return self._add_relation(
                request,
                pk,
                ShoppingCart,
                'Рецепт уже в корзине'
            )
        return self._delete_relation(
            request,
            pk,
            ShoppingCart,
            'Рецепт отсутствует в корзине'
        )

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        recipe = self.get_object()
        domain = request.build_absolute_uri('/')[:-1]
        short_link = f"{domain}/api/s/{recipe.short_code}"
        return Response({"short-link": short_link}, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        ingredients = self.get_ingredient(request.user)
        return self.generate_txt(data=ingredients, user=request.user)

    def get_ingredient(self, user):
        return RecipeIngredient.objects.filter(
            recipe__in_shopping_carts__user=user
        ).values(
            name=F('ingredient__name'),
            measurement_unit=F('ingredient__measurement_unit')
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

    def generate_txt(self, data, user):
        text = "Список покупок:\n"
        for item in data:
            text += (
                f"{item['name']} "
                f"({item['measurement_unit']}) — "
                f"{item['total_amount']}\n"
            )

        response = HttpResponse(text, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response
