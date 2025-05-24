import base64
import uuid
from django.core.files.base import ContentFile
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from djoser.views import UserViewSet as DjoserUserViewSet
from .models import User, Subscription
from .serializers import CustomUserSerializer, SubscriptionSerializer

class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        user = request.user
        author = self.get_object()
        if user == author:
            return Response({'error': 'Нельзя подписаться на себя'}, status=status.HTTP_400_BAD_REQUEST)
        subscription, created = Subscription.objects.get_or_create(user=user, author=author)
        if not created:
            return Response({'error': 'Подписка уже существует'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def unsubscribe(self, request, pk=None):
        user = request.user
        author = self.get_object()
        try:
            subscription = Subscription.objects.get(user=user, author=author)
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Subscription.DoesNotExist:
            return Response({'error': 'Подписка не найдена'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post', 'put', 'delete', 'get'], permission_classes=[IsAuthenticated], url_path='me/avatar')
    def avatar(self, request):
        if request.method in ['POST', 'PUT']:
            avatar_data = request.data.get('avatar')
            if not avatar_data:
                return Response({'error': 'Поле avatar обязательно'}, status=status.HTTP_400_BAD_REQUEST)
            if avatar_data.startswith('data:image'):
                try:
                    format, imgstr = avatar_data.split(';base64,')
                    ext = format.split('/')[-1]
                    filename = f'{uuid.uuid4()}.{ext}'
                    data = ContentFile(base64.b64decode(imgstr), name=filename)
                    # Удаляем старый файл, если есть
                    if request.user.avatar:
                        request.user.avatar.delete(save=False)
                    request.user.avatar.save(filename, data, save=True)
                except Exception as e:
                    return Response({'error': f'Ошибка обработки файла: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error': 'Формат avatar должен быть base64'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'avatar': request.user.avatar.url})

        if request.method == 'DELETE':
            if request.user.avatar:
                request.user.avatar.delete(save=False)
                request.user.avatar = None
                request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response({'avatar': request.user.avatar.url if request.user.avatar else None})
