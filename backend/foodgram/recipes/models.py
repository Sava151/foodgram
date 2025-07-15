from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator

from . import constants

User = get_user_model()


class Tag(models.Model):
    """Модель тега"""
    name = models.CharField(
        verbose_name='Название тега',
        unique=True,
        max_length=constants.TAG_MAX_LENGTH
    )
    slug = models.SlugField(
        verbose_name='Слаг тега',
        unique=True,
        max_length=constants.TAG_MAX_LENGTH
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиент"""
    name = models.CharField(
        verbose_name='Название',
        max_length=constants.INGREDIENT_MAX_LENGTH
    )
    measurement_unit = models.CharField(
        max_length=constants.INGREDIENT_M_UNIT_MAX_LENGTH,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipes(models.Model):
    """Модель рецепта"""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта'
    )
    name = models.CharField(
        max_length=constants.RECIPES_MAX_LENGTH,
        verbose_name='Название рецепта'
    )
    image = models.ImageField(
        upload_to='recipes/image/',
        verbose_name='Картинк рецепта'
    )
    text = models.TextField(verbose_name='Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=[
            MaxValueValidator(constants.RECIPES_MAX_COOKING_TIME),
            MinValueValidator(constants.RECIPES_MIN_COOKING_TIME)
        ]
    )
    short_code = models.CharField(
        max_length=constants.RECIPES_SHORT_CODE,
        unique=True,
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        default=timezone.now
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    "Промежуточная модель рецепта и ингредиента"
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients_recipe'
    )
    amount = models.IntegerField(
        verbose_name='Количество'
    )
