# Тесты приложения Announcements

## Тесты базовых функций объявлений (AnnouncementTests)

### Настройка тестов
- Создание тестового пользователя
- Создание тестовой категории
- Настройка клиента для тестирования

### Тесты CRUD операций
1. test_announcement_creation
   - Проверка создания объявления
   - Проверка корректности сохранения данных

2. test_announcement_update
   - Проверка обновления существующего объявления
   - Проверка корректности изменения данных

3. test_announcement_deletion
   - Проверка удаления объявления
   - Проверка отсутствия объявления после удаления

4. test_announcement_listing
   - Проверка отображения списка объявлений
   - Проверка количества объявлений в списке

5. test_announcement_search
   - Проверка поиска объявлений
   - Проверка фильтрации результатов поиска

## Тесты объявлений о животных (AnimalAnnouncementTests)

### Настройка тестов
- Создание тестового пользователя
- Создание тестовой категории для животных

### Тесты
1. test_animal_announcement_creation
   - Проверка создания объявления о животном
   - Проверка сохранения специфических полей для животных:
     - Вид животного
     - Порода
     - Возраст
     - Пол
     - Окрас
     - Вакцинация

## Тесты объявлений об услугах (ServiceAnnouncementTests)

### Настройка тестов
- Создание тестового пользователя-специалиста
- Создание тестовой категории для услуг

### Тесты
1. test_service_announcement_creation
   - Проверка создания объявления об услуге
   - Проверка сохранения специфических полей для услуг:
     - Тип услуги
     - Продолжительность
     - Местоположение 