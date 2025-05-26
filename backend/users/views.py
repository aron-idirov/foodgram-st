import base64
import uuid
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import filters
from djoser.views import UserViewSet as DjoserUserViewSet
from .models import User, Subscription
from .serializers import CustomUserSerializer, SubscriptionSerializer, SubscriptionCreateSerializer
from recipes.serializers import RecipeSerializer

class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email']
    lookup_field = 'id'  # Используем id вместо pk
    lookup_url_kwarg = 'id'  # URL-параметр будет называться id

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='me')
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)

        if request.method == 'POST':
            if user == author:
                return Response({'error': 'Нельзя подписаться на себя'}, status=status.HTTP_400_BAD_REQUEST)
            if Subscription.objects.filter(user=user, author=author).exists():
                return Response({'error': 'Подписка уже существует'}, status=status.HTTP_400_BAD_REQUEST)
            Subscription.objects.create(user=user, author=author)
            serializer = CustomUserSerializer(author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            subscription = Subscription.objects.filter(user=user, author=author)
            if subscription.exists():
                subscription.delete()
                return Response({'success': 'Подписка удалена'}, status=status.HTTP_204_NO_CONTENT)
            return Response({'error': 'Подписка не найдена'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated],     url_path='subscriptions')
    def subscriptions(self, request):
        queryset = Subscription.objects.filter(user=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SubscriptionSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = SubscriptionSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


    @action(detail=False, methods=['get', 'post', 'patch', 'put', 'delete'],     url_path='me/avatar', permission_classes=[IsAuthenticated])
    def avatar(self, request):
        user = request.user

        if request.method in ['PATCH', 'PUT', 'POST']:
            image_data = request.data.get('avatar')
            if not image_data:
                return Response({'error': 'Поле avatar обязательно.'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                format, imgstr = image_data.split(';base64,')
                ext = format.split('/')[-1]
                data = ContentFile(base64.b64decode(imgstr), name=f"{uuid.uuid4().hex}.{ext}")
                user.avatar.save(data.name, data, save=True)
                return Response({'avatar': request.build_absolute_uri(user.avatar.url)}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': f'Ошибка обработки изображения: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            user.avatar.delete(save=True)
            return Response({'success': 'Аватар удалён'})

        elif request.method == 'GET':
            if user.avatar:
                return Response({'avatar': request.build_absolute_uri(user.avatar.url)})
            return Response({'avatar': None})

        return Response({'message': 'Метод не разрешён'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

class SubscriptionViewSet(mixins.CreateModelMixin,
                          mixins.ListModelMixin,
                          viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return SubscriptionCreateSerializer
        return SubscriptionSerializer

    def perform_create(self, serializer):
        author_id = self.request.data.get('author')
        if not author_id:
            raise serializers.ValidationError("Поле 'author' обязательно.")
        if int(author_id) == self.request.user.id:
            raise serializers.ValidationError("Нельзя подписаться на себя.")
        if Subscription.objects.filter(user=self.request.user, author_id=author_id).exists():
            raise serializers.ValidationError("Подписка уже существует.")
        try:
            author = User.objects.get(id=author_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("Такой автор не существует.")
        serializer.save(user=self.request.user, author=author)
