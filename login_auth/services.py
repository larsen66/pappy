from django.conf import settings
from urllib.request import urlopen, URLError
from urllib.parse import quote
import logging
import random

logger = logging.getLogger(__name__)

class SMSService:
    """Сервис для отправки SMS сообщений через sms.ru API"""
    
    def __init__(self):
        self.api_id = settings.SMS_API_ID
        self.base_url = "http://sms.ru/sms/send"
        self.partner_id = "3805"
        self.test_mode = settings.SMS_TEST_MODE
        self.debug = settings.DEBUG
    
    def send_sms(self, phone: str, message: str) -> bool:
        """
        Отправка SMS сообщения
        
        Args:
            phone: Номер телефона в формате 79XXXXXXXXX
            message: Текст сообщения
            
        Returns:
            bool: True если сообщение успешно отправлено
        """
        # Убираем + из номера если есть
        phone = phone.replace('+', '')
        
        # В режиме отладки просто выводим сообщение в консоль
        if self.debug:
            print(f"\n{'='*50}")
            print(f"DEBUG: SMS Service")
            print(f"To: {phone}")
            print(f"Message: {message}")
            print(f"{'='*50}\n")
            return True
            
        # Если включен реальный SMS сервис
        if settings.SMS_ENABLED:
            try:
                # Формируем базовый URL
                url = f"{self.base_url}?api_id={self.api_id}&to={phone}&text={quote(message)}&partner_id={self.partner_id}"
                
                # Добавляем параметр test=1 если включен тестовый режим
                if self.test_mode:
                    url = f"{url}&test=1"
                    logger.info(f"SMS service is in TEST MODE. URL: {url}")
                
                response = urlopen(url, timeout=10)
                result = response.read().decode('utf-8').splitlines()
                
                if result and int(result[0]) == 100:
                    msg_id = result[1] if len(result) > 1 else 'N/A'
                    if self.test_mode:
                        logger.info(f"Test SMS sent successfully to {phone}. Test Message ID: {msg_id}")
                    else:
                        logger.info(f"SMS sent successfully to {phone}. Message ID: {msg_id}")
                    return True
                else:
                    error_code = result[0] if result else 'unknown'
                    logger.error(f"Failed to send {'test ' if self.test_mode else ''}SMS to {phone}. Error code: {error_code}")
                    return False
                    
            except URLError as e:
                logger.error(f"Failed to send {'test ' if self.test_mode else ''}SMS to {phone}. Error: {str(e)}")
                return False
            except Exception as e:
                logger.error(f"Unexpected error while sending {'test ' if self.test_mode else ''}SMS to {phone}. Error: {str(e)}")
                return False
        
        # Если SMS сервис отключен, просто логируем
        logger.info(f"SMS service is disabled. Would send to {phone}: {message}")
        return True

    @staticmethod
    def generate_code():
        """Генерация 4-значного кода"""
        return '{:04d}'.format(random.randint(0, 9999))

    @staticmethod
    def format_message(phone: str, code: str) -> str:
        """Форматирование SMS сообщения"""
        return (
            "\n==================================================\n"
            "[SMS] Код подтверждения для {}: {}\n"
            "==================================================\n"
        ).format(phone, code)

    @staticmethod
    def send_code(phone: str, code: str) -> bool:
        """
        Заглушка для отправки SMS.
        В реальном приложении здесь был бы код для отправки SMS через провайдера.
        """
        try:
            formatted_message = SMSService.format_message(phone, code)
            print(formatted_message)
            logger.info(f"SMS код отправлен на номер {phone}")
            return True
        except Exception as e:
            error_msg = f"Ошибка отправки SMS на номер {phone}: {str(e)}"
            logger.error(error_msg)
            return False 