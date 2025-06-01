import base64
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers
from .users_serializers import CustomUserSerializer
from recipes.models import Recipe, Tag, IngredientRecipe, Favorite, ShoppingCart
from ingredients.models import Ingredient


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            try:
                format, imgstr = data.split(";base64,")
                ext = format.split("/")[-1]
                id = uuid.uuid4().hex
                data = ContentFile(base64.b64decode(imgstr), name=f"{id}.{ext}")
            except Exception as e:
                raise serializers.ValidationError(f"Ошибка обработки изображения: {e}")
        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    AMOUNT_MIN = 1
    AMOUNT_MAX = 32000

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source="ingredient.id"
    )
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(source="ingredient.measurement_unit")
    amount = serializers.IntegerField(min_value=AMOUNT_MIN, max_value=AMOUNT_MAX)

    class Meta:
        model = IngredientRecipe
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeSerializer(serializers.ModelSerializer):
    COOKING_TIME_MIN = 1
    COOKING_TIME_MAX = 32000

    image = Base64ImageField(required=True)
    ingredients = IngredientInRecipeSerializer(source="ingredient_recipes", many=True)
    author = CustomUserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    cooking_time = serializers.IntegerField(
        min_value=COOKING_TIME_MIN, max_value=COOKING_TIME_MAX, required=True
    )

    class Meta:
        model = Recipe
        fields = [
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        ]

    def validate(self, data):
        ingredients_data = self.initial_data.get("ingredients", [])

        if not ingredients_data:
            raise serializers.ValidationError(
                {"ingredients": "Поле ingredients не может быть пустым."}
            )

        if ingredients_data is None and not self.partial:
            raise serializers.ValidationError(
                {"ingredients": "Поле ingredients не может быть пустым."}
            )

        ingredient_ids = [ingredient["id"] for ingredient in ingredients_data]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {"ingredients": "Ингредиенты не должны повторяться."}
            )

        if self.instance and not self.partial:  # Проверка для PATCH
            ingredients_data = self.initial_data.get("ingredients", [])
            if not ingredients_data:
                raise serializers.ValidationError(
                    {"ingredients": "Поле ingredients не может быть пустым."}
                )

        return data

    def _create_ingredients(self, recipe, ingredients_data):
        recipe.ingredient_recipes.all().delete()
        for ingredient_data in ingredients_data:
            IngredientRecipe.objects.create(
                recipe=recipe,
                ingredient=ingredient_data["ingredient"]["id"],
                amount=ingredient_data["amount"],
            )

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredient_recipes", [])
        tags_data = self.initial_data.get("tags", [])

        recipe = Recipe.objects.create(**validated_data)

        recipe.tags.set(tags_data)
        self._create_ingredients(recipe, ingredients_data)

        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("ingredient_recipes", None)
        tags_data = self.initial_data.get("tags", None)

        instance.name = validated_data.get("name", instance.name)
        instance.text = validated_data.get("text", instance.text)
        instance.cooking_time = validated_data.get(
            "cooking_time", instance.cooking_time
        )

        if "image" in validated_data:
            instance.image = validated_data.get("image", instance.image)

        instance.save()

        if tags_data is not None:
            instance.tags.set(tags_data)

        if ingredients_data is not None:
            self._create_ingredients(instance, ingredients_data)

        return instance

    def get_is_favorited(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return obj.in_favorites.filter(user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return obj.in_shopping_cart.filter(user=user).exists()


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
