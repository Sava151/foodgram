from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

from .constants import USER_MAX_LENGHT


class User(AbstractUser):
    """Модель Пользователя"""

    username_validator = RegexValidator(
        regex=r'^[\w.@+-]+\Z',
        message=(
            'Username содержит недопустимые символы. '
            'Допустимы: буквы, цифры, @/./+/-/_'
        )
    )
    username = models.CharField(
        max_length=USER_MAX_LENGHT,
        unique=True,
        verbose_name='Ник-нейм пользователя',
        validators=[username_validator]
    )
    email = models.EmailField(
        unique=True,
        verbose_name='Электроння почта'
    )
    first_name = models.CharField(
        max_length=USER_MAX_LENGHT,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=USER_MAX_LENGHT,
        verbose_name='Фамилия'
    )
    avatar = models.ImageField(
        upload_to='users/avatar/',
        null=True,
        default=None
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name'
    ]

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Follow(models.Model):
    "Модель подписок"
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        ordering = ('following',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

        constraints = [
            models.UniqueConstraint(
                fields=('following', 'user'),
                name='unique_following_user'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('following')),
                name='prevent_self_follow'
            )
        ]

    def __str__(self):
        return f'{self.user} подпиисан на автора {self.following}'


class Favorite(models.Model):
    "Модель избранного"
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    recipe = models.ForeignKey(
        'recipes.Recipes',
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite_item'
            )
        ]


class ShoppingCart(models.Model):
    """Модель корзины покупок"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_carts',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        'recipes.Recipes',
        on_delete=models.CASCADE,
        related_name='in_shopping_carts',
        verbose_name='Рецепт в корзине'
    )

    class Meta:
        verbose_name = 'Корзина для покупок'
        verbose_name_plural = 'Корзины для покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart_item'
            )
        ]
