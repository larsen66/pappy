# Обзор приложения Announcements

## Модели

### AnnouncementCategory
- Категории для объявлений
- Поля:
  - name: Название категории
  - slug: URL-совместимый идентификатор
  - parent: Родительская категория (для иерархии)

### Announcement (Базовая модель объявления)
- Поля:
  - title: Заголовок
  - description: Описание
  - price: Цена
  - category: Категория
  - type: Тип объявления (животное, услуга, вязка, потеряно/найдено)
  - status: Статус (активно, закрыто, на модерации)
  - author: Автор
  - location: Местоположение
  - created_at/updated_at: Даты создания/обновления
  - views_count: Счетчик просмотров
  - is_premium: Премиум-статус

### AnimalAnnouncement (Объявление о животном)
- Поля:
  - species: Вид животного
  - breed: Порода
  - age: Возраст
  - gender: Пол
  - size: Размер
  - color: Окрас
  - pedigree: Наличие родословной
  - vaccinated: Вакцинация
  - passport: Ветпаспорт
  - microchipped: Наличие чипа

### ServiceAnnouncement (Объявление об услуге)
- Поля:
  - service_type: Тип услуги (выгул, груминг, дрессировка и т.д.)
  - experience: Опыт работы
  - certificates: Сертификаты
  - schedule: График работы

### LostFoundAnnouncement (Объявление о потере/находке)
- Поля:
  - type: Тип (потеряно/найдено)
  - date_lost_found: Дата пропажи/находки
  - distinctive_features: Отличительные черты
  - location: Место пропажи/находки
  - contact_info: Контактная информация

### AnnouncementImage
- Поля:
  - announcement: Связь с объявлением
  - image: Изображение
  - is_main: Признак главного изображения

## Сервисы

### AreaNotificationService
- Отправка уведомлений пользователям в заданном радиусе
- Методы:
  - notify_users_in_radius: Отправка уведомлений в радиусе
  - _send_notification: Отправка конкретного уведомления

### LostPetMatchingService
- Поиск совпадений для потерянных/найденных животных
- Методы:
  - find_matches: Поиск потенциальных совпадений
  - _calculate_match_score: Расчет схожести объявлений
  - _get_match_reasons: Получение причин совпадения

### PetMatchingSystem
- Система сопоставления объявлений о пропаже/находке
- Методы:
  - get_image_features: Извлечение признаков из изображения
  - get_text_features: Извлечение признаков из текста
  - calculate_similarity: Расчет схожести объявлений
  - find_matches: Поиск похожих объявлений

## Представления (Views)

### Основные представления
- announcement_list: Список объявлений
- announcement_create: Создание объявления
- announcement_detail: Детали объявления
- announcement_edit: Редактирование объявления
- announcement_delete: Удаление объявления
- my_announcements: Мои объявления

### Специальные представления
- lost_pet_create: Создание объявления о пропаже
- lost_pet_detail: Детали пропавшего питомца
- lost_pets_map: Карта потерянных/найденных животных
- mating_create: Создание объявления о вязке
- mating_detail: Детали объявления о вязке
- mating_list: Список объявлений о вязке

## API Endpoints

### AnnouncementViewSet
- CRUD операции для объявлений
- Дополнительные действия:
  - close: Закрытие объявления
  - my: Получение своих объявлений

### AnimalAnnouncementViewSet
- CRUD операции для объявлений о животных

### ServiceAnnouncementViewSet
- CRUD операции для объявлений об услугах

### AnnouncementImageViewSet
- CRUD операции для изображений объявлений
- Дополнительные действия:
  - set_main: Установка главного изображения

## Фильтры и Поиск

### AnnouncementFilter
- Фильтрация по:
  - Цене (мин/макс)
  - Местоположению
  - Дате создания
  - Характеристикам животных
  - Типу услуг
