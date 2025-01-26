from django import forms
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
import re

class PhoneLoginForm(forms.Form):
    """Форма для ввода номера телефона"""
    
    phone_regex = RegexValidator(
        regex=r'^\+7\d{10}$',
        message=_('Номер телефона должен быть в формате: +7XXXXXXXXXX')
    )
    
    phone = forms.CharField(
        label=_('Номер телефона'),
        max_length=18,  # Увеличиваем максимальную длину для форматированного номера
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+7XXXXXXXXXX',
            'autocomplete': 'tel',
            'type': 'tel'
        })
    )
    
    def clean_phone(self):
        """Очистка и форматирование номера телефона"""
        phone = self.cleaned_data['phone']
        
        # Удаляем все кроме цифр и +
        phone = ''.join(c for c in phone if c in '+0123456789')
        
        # Проверяем и корректируем формат
        if phone.startswith('8'):
            phone = '+7' + phone[1:]
        elif not phone.startswith('+7'):
            phone = '+7' + phone.lstrip('+')
        
        # Проверяем длину и формат
        if not re.match(r'^\+7\d{10}$', phone):
            raise forms.ValidationError(_('Номер телефона должен быть в формате: +7XXXXXXXXXX'))
        
        return phone

class ConfirmationCodeForm(forms.Form):
    """Форма для ввода кода подтверждения"""
    
    code_regex = RegexValidator(
        regex=r'^\d{4}$',
        message=_('Код должен состоять из 4 цифр')
    )
    
    code = forms.CharField(
        label=_('Код подтверждения'),
        max_length=4,
        validators=[code_regex],
        widget=forms.TextInput(attrs={
            'class': 'form-control text-center',
            'placeholder': '1234',
            'autocomplete': 'off'
        })
    ) 