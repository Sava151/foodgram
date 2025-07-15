from django.db.models import F, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from rest_framework import mixins, viewsets, status
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    SAFE_METHODS
)
from rest_framework.response import Response
from rest_framework.views import APIView

from recipes.models import (
    Ingredient,
    Tag,
    Recipes,
    RecipeIngredient
)
from users.models import Favorite, Follow, ShoppingCart
from .filters import RecipeFilter
from .permission import AuthorOrReadOnly
from .pagination import CustomPagination
from .serializers import (
    AvatarSerializer,
    CurrentUserSerializer,
    CustomUserCreateSerializer,
    IngredientSerializer,
    PasswordChangeSerializer,
    RecipesListDetailSerializer,
    RecipeCreateUpdateSerializer,
    RecipeShortSerializer,
    TagSerializer,
    UserSerializer,
    UserSubscribeSerializer
)
from .viewset import ForUser

User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('id', 'name', 'slug')


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        search_query = self.request.query_params.get('name', '').strip()

        if not search_query:
            return queryset.none()

        startswith_query = Q(name__istartswith=search_query)
        contains_query = Q(name__icontains=search_query)

        startswith_results = queryset.filter(startswith_query)
        contains_results = queryset.filter(
            contains_query
        ).exclude(pk__in=startswith_results)
        return startswith_results.union(contains_results).order_by('name')[:20]


class UserViewSet(ForUser):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = LimitOffsetPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        return UserSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            {
                'request': self.request,
            }
        )
        return context


class CurrentUserViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = CurrentUserSerializer

    def get_object(self):
        return self.request.user


class AvatarViewSet(viewsets.GenericViewSet):
    serializer_class = AvatarSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        if user.avatar:
            user.avatar.delete(save=False)
        serializer = self.get_serializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()

        if user.avatar:
            user.avatar.delete(save=False)
            user.avatar = None
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscribeViewSet(viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = User.objects.all()
    pagination_class = CustomPagination

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, id=pk)
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

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        user = request.user
        following_ids = Follow.objects.filter(
            user=user
        ).values_list('following_id', flat=True)
        authors = User.objects.filter(id__in=following_ids)

        recipes_limit = request.query_params.get('recipes_limit')
        paginator = self.pagination_class()
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
    pagination_class = LimitOffsetPagination
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

    def perform_destroy(self, instance):
        instance.delete()

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        recipe = self.get_object()
        domain = request.build_absolute_uri('/')[:-1]
        short_link = f"{domain}/api/s/{recipe.short_code}"
        return Response({"short-link": short_link}, status=status.HTTP_200_OK)


class FavoriteViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipes, id=pk)
        if request.method == 'POST':
            favorite, created = Favorite.objects.get_or_create(
                user=request.user,
                recipe=recipe
            )
            if created:
                serializer = RecipeShortSerializer(
                    recipe,
                    context={'request': request}
                )
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {'status': 'Уже добавлено в избранное'},
                status=status.HTTP_400_BAD_REQUEST
            )

        elif request.method == 'DELETE':
            try:
                favorite = Favorite.objects.get(
                    user=request.user,
                    recipe=recipe
                )
            except Favorite.DoesNotExist:
                return Response(
                    {'detail': 'Рецепт отсутствует в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartViewSet(viewsets.ViewSet):
    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipes, pk=pk)
        if request.method == 'POST':
            if ShoppingCart.objects.filter(
                user=request.user,
                recipe=recipe
            ).exists():
                return Response(
                    {'detail': 'Рецепт уже в корзине'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeShortSerializer(
                recipe,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            try:
                cart_item = ShoppingCart.objects.get(
                    user=request.user,
                    recipe=recipe
                )
            except ShoppingCart.DoesNotExist:
                return Response(
                    {'detail': 'Рецепт отсутствует в корзине'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
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


class LogoutView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            request.user.set_password(
                serializer.validated_data['new_password'])
            request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShortCodeRedirect(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, short_code):
        recipe = get_object_or_404(Recipes, short_code=short_code)
        return redirect(f"/api/recipes/{recipe.pk}/")
