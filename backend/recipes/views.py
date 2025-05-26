from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from collections import defaultdict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Recipe, Favorite, ShoppingCart
from .serializers import RecipeSerializer, FavoriteSerializer, ShoppingCartSerializer

class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or obj.author == request.user

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'author__username']
    ordering_fields = ['created']
    ordering = ['-created']

    def get_queryset(self):
        queryset = Recipe.objects.all()
        user = self.request.user
        is_in_shopping_cart = self.request.query_params.get('is_in_shopping_cart')
        is_favorited = self.request.query_params.get('is_favorited')

        if user.is_authenticated:
            if is_in_shopping_cart in ['true', 'True', '1']:
                queryset = queryset.filter(in_shopping_cart__user=user)
            elif is_in_shopping_cart in ['false', 'False', '0']:
                queryset = queryset.exclude(in_shopping_cart__user=user)

            if is_favorited in ['true', 'True', '1']:
                queryset = queryset.filter(in_favorites__user=user)
            elif is_favorited in ['false', 'False', '0']:
                queryset = queryset.exclude(in_favorites__user=user)
        else:
            # Если пользователь неавторизован, игнорируем фильтры
            if is_in_shopping_cart or is_favorited:
                # Просто возвращаем все рецепты без фильтрации
                queryset = queryset

        return queryset.distinct()

    def perform_create(self, serializer):
        if not self.request.user or not self.request.user.is_authenticated:
            raise PermissionDenied('Неавторизованный пользователь не может создавать рецепты.')
        serializer.save(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user:
            return Response({'error': 'Удаление доступно только автору'}, status=status.HTTP_403_FORBIDDEN)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        recipe = self.get_object()
        if recipe.author != request.user:
            return Response({'error': 'Обновление чужого рецепта запрещено.'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=request.user, recipe=recipe).exists():
                return Response({'error': 'Рецепт уже в корзине'}, status=status.HTTP_400_BAD_REQUEST)
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            return Response({'success': 'Рецепт добавлен'}, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            cart_item = ShoppingCart.objects.filter(user=request.user, recipe=recipe)
            if cart_item.exists():
                cart_item.delete()
                return Response({'success': 'Рецепт удалён'}, status=status.HTTP_204_NO_CONTENT)
            return Response({'error': 'Рецепт не найден в корзине'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        # Получаем все покупки пользователя
        shopping_cart_items = ShoppingCart.objects.filter(user=request.user)

        # Словарь для подсчёта ингредиентов
        ingredient_summary = defaultdict(lambda: {'amount': 0, 'measurement_unit': ''})

        # Проходим по каждому рецепту в корзине
        for item in shopping_cart_items:
            recipe = item.recipe
            for ingredient in recipe.ingredient_recipes.all():
                key = ingredient.ingredient.name
                ingredient_summary[key]['amount'] += ingredient.amount
                ingredient_summary[key]['measurement_unit'] = ingredient.ingredient.measurement_unit

        # Формируем содержимое файла
        content = "Список покупок:\n\n"
        for ingredient_name, info in ingredient_summary.items():
            amount = info['amount']
            unit = info['measurement_unit']
            content += f"- {ingredient_name}: {amount} {unit}\n"

        # Отправляем файл
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'
        return response

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def view_shopping_cart(self, request):
        items = ShoppingCart.objects.filter(user=request.user).order_by('id')
        serializer = ShoppingCartSerializer(items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            if Favorite.objects.filter(user=request.user, recipe=recipe).exists():
                return Response({'error': 'Рецепт уже в избранном'}, status=status.HTTP_400_BAD_REQUEST)
            Favorite.objects.create(user=request.user, recipe=recipe)
            return Response({'success': 'Рецепт добавлен в избранное'}, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            favorite_item = Favorite.objects.filter(user=request.user, recipe=recipe)
            if favorite_item.exists():
                favorite_item.delete()
                return Response({'success': 'Рецепт удалён из избранного'}, status=status.HTTP_204_NO_CONTENT)
            return Response({'error': 'Рецепт не найден в избранном'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='get-link', permission_classes=[AllowAny])
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = f"https://foodgram.com/r/{recipe.pk}"
        return Response({'link': short_link})