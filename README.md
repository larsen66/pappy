
### 1. Открыть репозиторий

### 2. Создаем виртуальное окружение
```bash
# Создаем окружение
python -m venv venv

# Активируем окружение
# Для Mac/Linux:
source venv/bin/activate
# Для Windows:
.\venv\Scripts\activate
```

### 3. Устанавливаем все нужные пакеты
```bash
pip install -r requirements.txt
```

### 4. Настраиваем проект НЕ НУЖНО
НЕ ОБЯЗАТЕЛЬНО!!
1. Создайте файл `.env` в корневой папке проекта
2. Добавьте в него следующие настройки:
```
DEBUG=True
SECRET_KEY=your_secret_key
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 5. Настраиваем базу данных
```bash
python manage.py migrate
```

### 6. Создаем администратора
```bash
python manage.py createsuperuser
```

### 7. Настраиваем ngrok
1. Скачайте ngrok с сайта [https://ngrok.com/download]
2. Введите токен авторизации:
```bash
ngrok config add-authtoken 2YXc70E3DfxLsmIO5rF5EuO6x9C_5rwaxaae5Nt9nCnx2xjEQ
```

## Как запустить проект

### 1. Запускаем сервер Django
```bash
python manage.py runserver
```
Сервер запустится по адресу `http://127.0.0.1:8000/`

### 2. Запускаем ngrok
В новом окне терминала:
```bash
ngrok http 8000
```
Это создаст публичный URL для доступа к вашему серверу.

### Важные адреса
- Панель администратора: `http://127.0.0.1:8000/admin/`

## Решение проблем

### Если не устанавливаются пакеты:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Если проблемы с базой данных:
```bash
python manage.py makemigrations
python manage.py migrate
```

## Важно помнить
- Используйте сложные пароли для администратора
