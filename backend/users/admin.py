from django.contrib import admin
from .models import User, Subscription

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')

admin.site.register(User, UserAdmin)
admin.site.register(Subscription)
