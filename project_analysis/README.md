# Pappy - Платформа для животных

## О проекте

Pappy - это комплексная платформа для продажи животных, товаров для животных и услуг, связанных с животными. Платформа включает в себя функционал социальной сети, маркетплейса и сервиса для поиска потерянных животных.

## Требования

### Системные требования
- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Node.js 14+ (для фронтенда)

### Зависимости Python
- Django 4.2+
- Django REST Framework 3.14+
- Celery 5.2+
- Pillow 9.0+
- psycopg2-binary 2.9+

## Установка

1. Клонирование репозитория:
```bash
git clone https://github.com/your-repo/pappy.git
cd pappy
```

2. Создание виртуального окружения:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

3. Установка зависимостей:
```bash
pip install -r requirements.txt
```

4. Настройка переменных окружения:
```bash
cp .env.example .env
# Отредактируйте .env файл, добавив необходимые значения
```

5. Применение миграций:
```bash
python manage.py migrate
```

6. Создание суперпользователя:
```bash
python manage.py createsuperuser
```

7. Запуск сервера разработки:
```bash
python manage.py runserver
```

## Структура проекта

```
pappy/
├── announcements/     # Управление объявлениями
├── catalog/          # Каталог и поиск
├── chat/            # Система сообщений
├── login_auth/      # Аутентификация
├── matcher/         # Система подбора
├── moderation/      # Система модерации
├── pets/           # Управление животными
├── user_profile/   # Профили пользователей
├── static/         # Статические файлы
├── media/          # Загружаемые файлы
├── templates/      # HTML шаблоны
└── pappy/          # Основные настройки проекта
```

## Запуск тестов

### Запуск всех тестов:
```bash
python manage.py test
```

### Запуск тестов конкретного приложения:
```bash
python manage.py test app_name
```

### Запуск с покрытием:
```bash
coverage run manage.py test
coverage report
```

## Дополнительные сервисы

### Redis
```bash
redis-server
```

### Celery
```bash
celery -A pappy worker -l info
celery -A pappy beat -l info
```

## API документация

API документация доступна по адресу:
```
http://localhost:8000/api/docs/
```

## Переменные окружения

Основные переменные окружения:

```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://user:password@localhost:5432/pappy
REDIS_URL=redis://localhost:6379/0
SMS_API_KEY=your-sms-api-key
GOSUSLUGI_CLIENT_ID=your-client-id
GOSUSLUGI_SECRET=your-secret
```

## Развертывание

### Docker
```bash
docker-compose up -d
```

### Ручное развертывание
1. Настройте веб-сервер (nginx/apache)
2. Настройте WSGI-сервер (gunicorn/uwsgi)
3. Настройте SSL-сертификат
4. Настройте базу данных
5. Настройте Redis
6. Запустите Celery workers

## Мониторинг

- Sentry для отслеживания ошибок
- Prometheus + Grafana для метрик
- ELK Stack для логов

## Разработка

### Создание миграций
```bash
python manage.py makemigrations
```

### Применение миграций
```bash
python manage.py migrate
```

### Сбор статики
```bash
python manage.py collectstatic
```

