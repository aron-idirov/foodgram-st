from rest_framework import serializers
from djoser.serializers import UserCreateSerializer, UserSerializer
from .models import User, Subscription

class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'password')

class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(required=False, allow_null=True)

    class Meta(UserSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'avatar', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request', None)
        if request is None or not hasattr(request, 'user') or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(user=request.user, author=obj).exists()

class SubscriptionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='author.id')
    username = serializers.CharField(source='author.username')
    first_name = serializers.CharField(source='author.first_name')
    last_name = serializers.CharField(source='author.last_name')
    email = serializers.EmailField(source='author.email')
    avatar = serializers.ImageField(source='author.avatar')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'avatar', 'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        from recipes.serializers import RecipeSerializer
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes_qs = obj.author.recipes.all()
        if recipes_limit:
            recipes_qs = recipes_qs[:int(recipes_limit)]
        return RecipeSerializer(recipes_qs, many=True, context={'request': request}).data

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()
    
    def get_is_subscribed(self, obj):
        return True

class SubscriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('author',)
