import base64
import uuid
from rest_framework import serializers
from django.db import IntegrityError
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer
from django.utils.crypto import get_random_string

from recipes.models import Ingredient, Recipes, RecipeIngredient, Tag
from users.models import Favorite, Follow, ShoppingCart

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            file_name = f"{uuid.uuid4()}.{ext}"
            decoded_file = base64.b64decode(imgstr)
            data = ContentFile(decoded_file, name=file_name)
        return super().to_internal_value(data)


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
        if request and request.user.is_authenticated:
            return Follow.objects.filter(
                user=request.user,
                following=obj
            ).exists()
        return False

    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None


class CurrentUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        return False


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)
        extra_kwargs = {
            'avatar': {'required': True}
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.avatar:
            representation['avatar'] = instance.avatar.url
        else:
            representation['avatar'] = None

        return representation


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
            return self.context['request'].build_absolute_uri(obj.image.url)
        return None


class UserSubscribeSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        )

    def get_is_subscribed(self, obj):
        return True

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

    def get_avatar(self, obj):
        if obj.avatar:
            return self.context['request'].build_absolute_uri(obj.avatar.url)
        return None


class SaveRecipeIngredientSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer()

    class Meta:
        model = RecipeIngredient
        fields = ('ingredient', 'amount')

    def to_representation(self, instance):
        representat = super().to_representation(instance)
        return {
            'id': representat['ingredient']['id'],
            'name': representat['ingredient']['name'],
            'measurement_unit': representat['ingredient']['measurement_unit'],
            'amount': representat['amount']
        }


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
        if not obj.image:
            return None
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(obj.image.url)

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False


class IngredientAmountSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField()

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'Количество ингредиента не может быть меньше или равно нулю'
            )
        return value


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = IngredientAmountSerializer(
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
            'author'
        )

    def validate(self, attrs):
        is_update = self.instance is not None
        if is_update:
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
            ingred = elem['id']
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
        check_set = set()
        for tags in value:
            if tags not in check_set:
                check_set.add(tags)
            else:
                raise serializers.ValidationError(
                    'Теги должны быть уникальны'
                )
        return value

    def create_ingredients(self, recipe, ingredients):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            ) for ingredient in ingredients
        ])

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        while True:
            short_code = get_random_string(length=20)
            try:
                recipe = Recipes.objects.create(
                    short_code=short_code,
                    **validated_data
                )
                break
            except IntegrityError:
                continue
        recipe.tags.set(tags_data)
        self.create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)
        instance = super().update(instance, validated_data)
        if tags_data is not None:
            instance.tags.set(tags_data)
        if ingredients_data is not None:
            RecipeIngredient.objects.filter(recipe=instance).delete()
            self.create_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        return RecipesListDetailSerializer(instance, context=self.context).data


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Текущий пароль неверен")
        return value
