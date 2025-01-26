from django.conf import settings
from django.core.exceptions import ValidationError
import requests
import json
from typing import Dict, Optional

class GosuslugiAuth:
    """Заглушка для работы с OAuth авторизацией через Госуслуги"""
    
    def __init__(self):
        self.is_test_mode = True
        self.test_user_data = {
            'id': '1234567890',
            'phone': '+79991234567',
            'email': 'test@example.com',
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'is_verified': True
        }
    
    def initialize_auth(self) -> str:
        """Заглушка для инициализации OAuth flow"""
        return '/auth/gosuslugi/callback/?code=test_code'
    
    def handle_callback(self, code: str) -> dict:
        """Заглушка для обработки ответа от Госуслуг"""
        if code == 'test_code':
            return {
                'access_token': 'test_token',
                'token_type': 'Bearer',
                'expires_in': 3600
            }
        raise ValidationError('Неверный код авторизации')
    
    def get_user_data(self, token: str) -> dict:
        """Заглушка для получения данных пользователя"""
        if token == 'test_token':
            return self.test_user_data
        raise ValidationError('Неверный токен')
    
    def verify_token(self, token: str) -> bool:
        """Заглушка для проверки валидности токена"""
        return token == 'test_token' 