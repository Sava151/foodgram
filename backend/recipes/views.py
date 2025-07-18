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
                f"http://foodgram151.zapto.org/recipes/{recipe.pk}/"
            )
        except Recipes.DoesNotExist:
            return redirect('http://foodgram151.zapto.org/not-found')
