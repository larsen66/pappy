# Тесты приложения Matcher

## Тесты моделей

### Тесты UserPreferences
- Создание предпочтений пользователя
- Валидация диапазона возраста
- Проверка значений по умолчанию
- Обновление предпочтений

### Тесты MatchingScore
- Создание оценок совместимости
- Уникальность пар пользователь-животное
- Проверка индексов
- Очистка старых записей

### Тесты UserInteraction
- Создание разных типов взаимодействий
- Проверка временных меток
- Валидация типов взаимодействий
- Проверка индексов

### Тесты RecommendationHistory
- Сохранение рекомендаций
- Отметка о взаимодействиях
- Проверка причин рекомендаций
- Очистка старых записей

## Тесты сервисов

### Тесты MatchingService

#### Расчет базовой оценки:
- Проверка начисления баллов за совпадения
- Проверка специальных требований
- Расчет итоговой оценки

#### Бонус за расположение:
- Расчет расстояния
- Применение бонуса
- Проверка максимального расстояния

#### Бонус за взаимодействия:
- Учет истории лайков
- Расчет бонуса
- Проверка похожих видов

### Тесты RecommendationService

#### Коллаборативные рекомендации:
- Поиск похожих пользователей
- Получение рекомендаций
- Проверка релевантности

#### Контентные рекомендации:
- Анализ предыдущих лайков
- Поиск похожих животных
- Проверка релевантности

#### Смешанные рекомендации:
- Объединение рекомендаций
- Сортировка результатов
- Сохранение истории

## Тесты форм

### Тесты UserPreferencesForm
- Валидация полей формы
- Динамическая загрузка списков
- Проверка обязательных полей
- Обработка ошибок валидации

## Тесты представлений

### Тесты обновления предпочтений:
- GET-запрос формы
- POST-запрос с валидными данными
- POST-запрос с невалидными данными
- Проверка редиректов

### Тесты списка совпадений:
- Получение списка
- Проверка пагинации
- Проверка сортировки
- Фильтрация результатов

### Тесты списка рекомендаций:
- Получение рекомендаций
- Проверка пагинации
- Проверка типов рекомендаций
- Проверка порядка

### Тесты записи взаимодействий:
- Создание взаимодействий
- Валидация типов
- Обработка ошибок
- Проверка ответов

### Тесты истории взаимодействий:
- Получение истории
- Проверка пагинации
- Проверка сортировки
- Фильтрация по типам

## Как запускать тесты

### Все тесты приложения:
```bash
python manage.py test matcher
```

### Тесты моделей:
```bash
python manage.py test matcher.tests.test_models
```

### Тесты сервисов:
```bash
python manage.py test matcher.tests.test_services
```

### Тесты форм:
```bash
python manage.py test matcher.tests.test_forms
```

### Тесты представлений:
```bash
python manage.py test matcher.tests.test_views
``` 