from django import forms
from django.utils.translation import gettext_lazy as _
from .models import NotificationPreference

class NotificationPreferenceForm(forms.ModelForm):
    """Форма настроек уведомлений"""
    
    class Meta:
        model = NotificationPreference
        fields = [
            'email_new_matches',
            'email_new_messages',
            'email_status_updates',
            'email_recommendations',
            'email_lost_pets',
            'push_new_matches',
            'push_new_messages',
            'push_status_updates',
            'push_recommendations',
            'push_lost_pets',
            'email_frequency',
            'quiet_hours_start',
            'quiet_hours_end',
            'lost_pets_radius',
        ]
        widgets = {
            'quiet_hours_start': forms.TimeInput(attrs={'type': 'time'}),
            'quiet_hours_end': forms.TimeInput(attrs={'type': 'time'}),
            'lost_pets_radius': forms.NumberInput(attrs={
                'min': 0,
                'max': 100,
                'step': 1
            })
        }
        help_texts = {
            'email_frequency': _('Как часто отправлять email-уведомления'),
            'quiet_hours_start': _('Начало периода тишины (push-уведомления не будут отправляться)'),
            'quiet_hours_end': _('Конец периода тишины'),
            'lost_pets_radius': _('Радиус в километрах для уведомлений о потерянных животных поблизости'),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Проверяем, что хотя бы один тип уведомлений включен для каждой категории
        email_notifications = any([
            cleaned_data.get('email_new_matches'),
            cleaned_data.get('email_new_messages'),
            cleaned_data.get('email_status_updates'),
            cleaned_data.get('email_recommendations'),
            cleaned_data.get('email_lost_pets'),
        ])
        
        push_notifications = any([
            cleaned_data.get('push_new_matches'),
            cleaned_data.get('push_new_messages'),
            cleaned_data.get('push_status_updates'),
            cleaned_data.get('push_recommendations'),
            cleaned_data.get('push_lost_pets'),
        ])
        
        if not email_notifications and not push_notifications:
            raise forms.ValidationError(
                _('Необходимо включить хотя бы один тип уведомлений')
            )
        
        # Проверяем корректность периода тишины
        quiet_start = cleaned_data.get('quiet_hours_start')
        quiet_end = cleaned_data.get('quiet_hours_end')
        if quiet_start and quiet_end and quiet_start >= quiet_end:
            raise forms.ValidationError(
                _('Время начала периода тишины должно быть меньше времени окончания')
            )
        
        # Проверяем радиус для уведомлений о потерянных животных
        radius = cleaned_data.get('lost_pets_radius')
        if radius is not None and radius < 0:
            raise forms.ValidationError(
                _('Радиус не может быть отрицательным')
            )
        
        return cleaned_data 