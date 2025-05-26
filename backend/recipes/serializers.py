import base64
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers
from users.serializers import CustomUserSerializer
from .models import Recipe, Tag, IngredientRecipe, Favorite, ShoppingCart
from ingredients.models import Ingredient

class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1]
                id = uuid.uuid4().hex
                data = ContentFile(base64.b64decode(imgstr), name=f"{id}.{ext}")
            except Exception as e:
                raise serializers.ValidationError(f"Ошибка обработки изображения: {e}")
        return super().to_internal_value(data)

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'

class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all(), source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def validate_amount(self, value):
        if value < 1:
            raise serializers.ValidationError('Количество ингредиента должно быть не менее 1.')
        return value

class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=True)
    ingredients = IngredientInRecipeSerializer(source='ingredient_recipes', many=True)
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = '__all__'

    def validate(self, data):
        ingredients_data = self.initial_data.get('ingredients', [])

        if not ingredients_data:
            raise serializers.ValidationError({'ingredients': 'Поле ingredients не может быть пустым.'})

        if ingredients_data is None and not self.partial:
            raise serializers.ValidationError({'ingredients': 'Поле ingredients не может быть пустым.'})

        ingredient_ids = [ingredient['id'] for ingredient in ingredients_data]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError({'ingredients': 'Ингредиенты не должны повторяться.'})

        if self.instance and not self.partial:  # Проверка для PATCH
            ingredients_data = self.initial_data.get('ingredients', [])
            if not ingredients_data:
                raise serializers.ValidationError({'ingredients': 'Поле ingredients не может быть пустым.'})

        cooking_time = data.get('cooking_time')
        if cooking_time is not None and cooking_time < 1:
            raise serializers.ValidationError({'cooking_time': 'Время приготовления должно быть больше или равно 1.'})

        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredient_recipes', [])
        tags_data = self.initial_data.get('tags', [])
        
        print("CREATE: validated_data:", validated_data)
        print("CREATE: ingredients_data:", ingredients_data)
        print("CREATE: tags_data:", tags_data)
        
        recipe = Recipe.objects.create(**validated_data)
        
        for tag_id in tags_data or []:
            recipe.tags.add(tag_id)
        
        for ingredient_data in ingredients_data or []:
            try:
                IngredientRecipe.objects.create(
                    recipe=recipe,
                    ingredient=ingredient_data['ingredient']['id'],
                    amount=ingredient_data['amount']
                )
            except Exception as e:
                print("Ошибка создания IngredientRecipe:", e)
        
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredient_recipes', None)
        tags_data = self.initial_data.get('tags', None)

        print("UPDATE: validated_data:", validated_data)
        print("UPDATE: ingredients_data:", ingredients_data)
        print("UPDATE: tags_data:", tags_data)
        
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time', instance.cooking_time)
        
        if 'image' in validated_data:
            instance.image = validated_data.get('image', instance.image)

        instance.save()

        if tags_data is not None:
            instance.tags.set(tags_data)

        if ingredients_data is not None:
            instance.ingredient_recipes.all().delete()
            for ingredient_data in ingredients_data:
                try:
                    IngredientRecipe.objects.create(
                        recipe=instance,
                        ingredient=ingredient_data['ingredient']['id'],
                        amount=ingredient_data['amount']
                    )
                except Exception as e:
                    print("Ошибка обновления IngredientRecipe:", e)
        
        return instance

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return obj.in_favorites.filter(user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return obj.in_shopping_cart.filter(user=user).exists()

class ShoppingCartSerializer(serializers.ModelSerializer):
    recipe = RecipeSerializer(read_only=True)

    class Meta:
        model = ShoppingCart
        fields = ('id', 'recipe', 'created_at')

class FavoriteSerializer(serializers.ModelSerializer):
    recipe = RecipeSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ('id', 'recipe', 'created_at')
