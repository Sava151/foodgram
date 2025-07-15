import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    # python manage.py load_ingredients
    # docker compose exec backend python manage.py load_ingredients
    hepl = "Загружает JSON-данные об ингредиентах в базу"

    def handle(self, *args, **options):
        file_path = os.path.join(
            settings.BASE_DIR,
            'fixtures',
            'ingredients.json'
        )
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            ingredients_to_create = []
            for item in data:
                ingredients_to_create.append(
                    Ingredient(
                        name=item['name'],
                        measurement_unit=item['measurement_unit']
                    )
                )
            Ingredient.objects.bulk_create(ingredients_to_create)
        self.stdout.write(self.style.SUCCESS('Данные загружены!'))
