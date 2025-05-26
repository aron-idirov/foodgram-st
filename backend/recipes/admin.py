from django.contrib import admin
from .models import Recipe, Tag, IngredientRecipe, Favorite


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorites_count')
    search_fields = ('name', 'author__username')
    list_filter = ('author', 'tags')

    def favorites_count(self, obj):
        return obj.in_favorites.count()
    favorites_count.short_description = 'Количество в избранном'


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag)
admin.site.register(IngredientRecipe)
admin.site.register(Favorite)
