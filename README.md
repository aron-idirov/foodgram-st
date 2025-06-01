# Foodgram — Продуктовый помощник

## Описание
Foodgram — это веб-приложение для публикации рецептов, добавления их в избранное и формирования списка покупок. Пользователи могут подписываться на авторов, добавлять рецепты в корзину и скачивать список покупок.

## Технологии
- Backend: Django, Django REST Framework
- Frontend: React
- База данных: PostgreSQL
- Docker, Docker Compose
- GitHub Actions для CI/CD

---

## Вариант 1: Локальная сборка из GitHub

### Клонирование репозитория
bash  
git clone https://github.com/yourusername/foodgram.git  
cd foodgram  

### Запуск (локально)
docker-compose up --build  

Приложение будет доступно по адресам:  
Backend: http://localhost/api  
Frontend: http://localhost  

## Вариант 2: Запуск с образами из Docker Hub

### Образы
  backend:  
    image: fur911/foodgram-backend:latest  
  frontend:  
    image: fur911/foodgram-frontend:latest  

### Подготовьте docker-compose
Пример docker-compose можно найти в /infra  
