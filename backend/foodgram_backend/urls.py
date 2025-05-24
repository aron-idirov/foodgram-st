from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.authtoken')),
    path('api/users/', include('users.urls')),
    path('api/recipes/', include('recipes.urls')),
    path('api/favorites/', include('favorites.urls')),
    path('api/', lambda request: JsonResponse({'message': 'API root'})),
]

