from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import re
from .models import User

def clean_phone_number(phone):
    """Очистка и форматирование номера телефона"""
    # Убираем все кроме цифр
    cleaned = re.sub(r'\D', '', phone)
    
    # Проверяем длину
    if len(cleaned) < 10 or len(cleaned) > 11:
        raise ValidationError('Неверный формат номера телефона')
    
    # Если номер начинается с 8 или 7, это российский номер
    if len(cleaned) == 11 and cleaned[0] in ['7', '8']:
        cleaned = '7' + cleaned[1:]
    # Если номер без кода страны, добавляем 7
    elif len(cleaned) == 10:
        cleaned = '7' + cleaned
    
    # Форматируем номер в красивый вид
    return f'+{cleaned}'

class PhoneLoginForm(forms.Form):
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+7 (999) 123-45-67',
            'type': 'tel',
            'pattern': '[+][0-9]{1,3}[(][0-9]{3}[)][0-9]{3}[-][0-9]{2}[-][0-9]{2}',
        })
    )

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        try:
            return clean_phone_number(phone)
        except ValidationError as e:
            raise forms.ValidationError('Пожалуйста, введите корректный номер телефона')

class SMSVerificationForm(forms.Form):
    code = forms.CharField(
        max_length=4,
        min_length=4,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '0000',
            'pattern': '[0-9]*',
            'inputmode': 'numeric',
            'autocomplete': 'one-time-code'
        })
    )
    phone = forms.CharField(widget=forms.HiddenInput())  # Для сохранения контекста 

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if not code.isdigit():
            raise forms.ValidationError('Код должен содержать только цифры')
        return code 