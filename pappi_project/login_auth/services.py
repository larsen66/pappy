import logging
import random
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger('zaglushka')
console_logger = logging.getLogger('console')

class SMSService:
    @staticmethod
    def generate_code():
        """Генерация 4-значного кода"""
        return '{:04d}'.format(random.randint(0, 9999))

    @staticmethod
    def send_code(phone: str, code: str) -> bool:
        """
        Заглушка для отправки SMS.
        В реальном приложении здесь был бы код для отправки SMS через провайдера.
        """
        try:
            formatted_message = (
                "\n==================================================\n"
                "SMS Code Verification\n"
                f"Phone: {phone}\n"
                f"Code: {code}\n"
                "==================================================\n"
            )
            print(formatted_message)
            console_logger.info(f"SMS код отправлен на номер {phone}")
            return True
        except Exception as e:
            error_msg = f"Ошибка отправки SMS на номер {phone}: {str(e)}"
            logger.error(error_msg)
            console_logger.error(error_msg)
            return False

class GosuslugiService:
    @staticmethod
    def authenticate(token: str) -> dict:
        """
        Заглушка для аутентификации через Госуслуги.
        В реальном приложении здесь был бы код для проверки токена и получения данных пользователя.
        """
        try:
            # Возвращаем тестовые данные
            return {
                'phone': '+79991234567',
                'first_name': 'Тест',
                'last_name': 'Тестов',
                'middle_name': 'Тестович',
                'snils': '123-456-789 00',
                'inn': '1234567890',
                'email': 'test@test.ru'
            }
        except Exception as e:
            error_msg = f"Ошибка аутентификации через Госуслуги: {str(e)}"
            logger.error(error_msg)
            console_logger.error(error_msg)
            raise 