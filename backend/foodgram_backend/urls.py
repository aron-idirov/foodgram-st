from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from ingredients.views import IngredientViewSet
from recipes.views import RecipeViewSet
from users.views import UserViewSet
# Добавь другие ViewSet по мере необходимости

router = DefaultRouter()
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'users', UserViewSet, basename='users')
# Добавь остальные маршруты (например, tags, subscriptions) при необходимости

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.authtoken')),
]
