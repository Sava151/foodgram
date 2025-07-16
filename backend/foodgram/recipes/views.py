from django.shortcuts import get_object_or_404, redirect
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .models import Recipes


class ShortCodeRedirect(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, short_code):
        recipe = get_object_or_404(Recipes, short_code=short_code)
        return redirect(f"/api/recipes/{recipe.pk}/")
