from django.conf import settings
from django.shortcuts import redirect
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from .models import Recipes


class ShortCodeRedirect(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, short_code):
        try:
            recipe = Recipes.objects.get(short_code=short_code)
            return redirect(
                f"https://{settings.DOMAIN}/recipes/{recipe.pk}/"
            )
        except Recipes.DoesNotExist:
            return redirect(f'http://{settings.DOMAIN}/not-found')
