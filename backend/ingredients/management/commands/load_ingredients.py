from django.core.management.base import BaseCommand
from ingredients.models import Ingredient
import json
import os


class Command(BaseCommand):
    help = 'Загружает ингредиенты из файла data/ingredients.json'

    def handle(self, *args, **kwargs):
        # Определяем путь к файлу относительно папки manage.py
        file_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), '../../../data/ingredients.json'))
        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f'Файл {file_path} не найден.'))
            return

        with open(file_path, encoding='utf-8') as f:
            data = json.load(f)
            count = 0
            for item in data:
                ingredient, created = Ingredient.objects.get_or_create(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                )
                if created:
                    count += 1
            self.stdout.write(self.style.SUCCESS(
                f'Загружено {count} новых ингредиентов'))
