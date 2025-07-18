from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from .serializers_fields import Base64ImageField
from recipes.models import Ingredient, Recipes, RecipeIngredient, Tag
from users.models import Favorite, Follow, ShoppingCart

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = (
            'name',
            'measurement_unit',
            'id',
        )


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (
            request is not None
            and request.user.is_authenticated
            and Follow.objects.filter(
                user=request.user,
                following=obj
            ).exists()
        )

    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)
        extra_kwargs = {
            'avatar': {'required': True}
        }

    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None


class RecipeShortSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipes
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None


class UserSubscribeSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        )

    def get_recipes(self, obj):
        recipes_limit = self.context.get('recipes_limit')
        recipes = obj.recipes.all()

        if recipes_limit and recipes_limit.isdigit():
            recipes = recipes[:int(recipes_limit)]
        else:
            recipes = recipes

        return RecipeShortSerializer(
            recipes,
            many=True,
            context={'request': self.context.get('request')}
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SaveRecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipesListDetailSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserSerializer()
    ingredients = SaveRecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipes
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (
            request is not None
            and request.user.is_authenticated
            and ShoppingCart.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (
            request is not None
            and request.user.is_authenticated
            and Favorite.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        )


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = SaveRecipeIngredientSerializer(
        many=True,
    )
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipes
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
            'author',
        )

    def validate(self, attrs):
        if 'ingredients' not in attrs:
            raise serializers.ValidationError(
                {'ingredients': 'Это поле обязательно при обновлении'}
            )
        if 'tags' not in attrs:
            raise serializers.ValidationError(
                {'tags': 'Это поле обязательно при обновлении'}
            )
        return super().validate(attrs)

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError('Добавьте минимум 1 ингредиент')
        check_set = set()
        for elem in value:
            ingred = elem['ingredient'].id
            if ingred not in check_set:
                check_set.add(ingred)
            else:
                raise serializers.ValidationError(
                    'Ингредиенты должны быть уникальны'
                )
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError('Добавьте минимум 1 тег')
        check_set = set(value)
        if len(value) != len(check_set):
            raise serializers.ValidationError(
                'Теги должны быть уникальны'
            )
        return value

    def create_ingredients(self, recipe, ingredients):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            ) for ingredient in ingredients
        ])

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipes.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        self.create_ingredients(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        instance = super().update(instance, validated_data)
        instance.tags.set(tags_data)
        instance.ingredients.clear()
        self.create_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        return RecipesListDetailSerializer(
            instance,
            context=self.context,
        ).data
