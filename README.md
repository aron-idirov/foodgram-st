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
```bash
git clone https://github.com/yourusername/foodgram.git
cd foodgram

### Запуск (локально)
docker-compose up --build

Приложение будет доступно по адресам:
Backend: http://localhost/api
Frontend: http://localhost

## Вариант 2: Запуск с образами из Docker Hub

### Подготовьте docker-compose.yml (пример)

version: '3.8'

services:
  db:
    image: postgres:13
    container_name: foodgram-db
    restart: always
    environment:
      POSTGRES_DB: foodgram
      POSTGRES_USER: foodgram_user
      POSTGRES_PASSWORD: supersecret
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    container_name: foodgram-backend
    build: ../backend
    restart: always
    env_file:
      - .env
    depends_on:
      - db
    volumes:
      - ../backend:/app
      - ../data:/app/data  # Для загрузки ingredients.json
      - static:/app/static
      - media:/app/media
    ports:
      - "8000:8000"
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             gunicorn foodgram_backend.wsgi:application --bind 0.0.0.0:8000"

  frontend:
    container_name: foodgram-frontend
    build: ../frontend
    restart: "no"
    volumes:
      - frontend_build:/app/build  # Монтируем реальную папку build
    command: sh -c "npm install --legacy-peer-deps && npm run build"

  nginx:
    container_name: foodgram-proxy
    image: nginx:1.25.4-alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - static:/static
      - media:/media
      - frontend_build:/usr/share/nginx/html  # Монтируем build
      - ../docs/:/usr/share/nginx/html/api/docs/
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
  static:
  media:
  frontend_build:

### Образы

  backend:
    image: fur911/foodgram-backend:latest
  frontend:
    image: fur911/foodgram-frontend:latest

