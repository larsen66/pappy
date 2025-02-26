# Что мы тестируем в приложении Catalog

## Тесты моделей (test_models.py)

### Тесты категорий (CategoryModelTest)
Мы проверяем:
- Правильность создания иерархии категорий (родитель-потомок)
- Корректное отображение названий категорий
- Автоматическую генерацию slug из русских названий

### Тесты товаров (ProductModelTest)
Мы тестируем:
- Создание товара со всеми обязательными полями
- Правильность работы статусов товара:
  - active (активный)
  - pending (на модерации)
  - blocked (заблокирован)
  - archived (в архиве)

### Тесты изображений (ProductImageModelTest)
Проверяем:
- Загрузку нескольких изображений для товара
- Корректную работу с главным изображением:
  - Только одно изображение может быть главным
  - При смене главного изображения старое перестает быть главным

### Тесты избранного (FavoriteModelTest)
Тестируем:
- Добавление товара в избранное
- Удаление из избранного
- Защиту от дублирования (один товар нельзя добавить в избранное дважды)

## Тесты форм (test_forms.py)

### ProductForm
Проверяем:
- Валидацию обязательных полей
- Загрузку изображений
- Автоматическое создание slug

### ProductFilterForm
Тестируем работу фильтров:
- По категориям
- По цене
- По состоянию товара
- Сортировку результатов

## Тесты представлений (test_views.py)

### Основные страницы
Проверяем:
- Главную страницу каталога
- Страницу категории
- Страницу товара
- Поиск товаров

### Операции с товарами
Тестируем:
- Создание товара
- Редактирование товара
- Удаление товара
- Управление статусами

### Избранное
Проверяем:
- Добавление в избранное
- Удаление из избранного
- Просмотр списка избранного

## Тесты потерянных питомцев (test_lostfound.py)

### Создание объявлений
Тестируем:
- Создание объявления о пропаже
- Валидацию обязательных полей
- Загрузку фотографий

### Поиск и уведомления
Проверяем:
- Поиск по базе потеряшек
- Отправку уведомлений в радиусе
- Связь с владельцем

## Тесты вязки (test_mating.py)

### Запросы на вязку
Тестируем:
- Создание запроса
- Проверку совместимости питомцев
- Отмену запроса

### Совпадения
Проверяем:
- Обработку взаимных лайков
- Создание диалога при совпадении
- Уведомления о совпадениях 