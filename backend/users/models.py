from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    email = models.EmailField(unique=True, max_length=254)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']


class Subscription(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='subscriptions_set')
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='subscribers_set')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'author')

    def __str__(self):
        return f"{self.user} подписан на {self.author}"
