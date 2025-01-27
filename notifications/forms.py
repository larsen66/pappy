from django import forms
from django.utils.translation import gettext_lazy as _
from .models import NotificationPreference

class NotificationPreferenceForm(forms.ModelForm):
    """Форма настроек уведомлений"""
    
    class Meta:
        model = NotificationPreference
        fields = [
            'email_enabled',
            'push_enabled',
            'email_frequency',
            'quiet_hours_start',
            'quiet_hours_end',
            'notify_new_matches',
            'notify_messages',
            'notify_status_updates',
            'notify_lost_pets_radius',
            'notify_lost_pets_enabled',
        ]
        widgets = {
            'quiet_hours_start': forms.TimeInput(attrs={'type': 'time'}),
            'quiet_hours_end': forms.TimeInput(attrs={'type': 'time'}),
            'notify_lost_pets_radius': forms.NumberInput(attrs={
                'min': 0,
                'max': 100,
                'step': 1
            })
        }
        help_texts = {
            'email_frequency': _('Как часто отправлять email-уведомления'),
            'quiet_hours_start': _('Начало периода тишины (push-уведомления не будут отправляться)'),
            'quiet_hours_end': _('Конец периода тишины'),
            'notify_lost_pets_radius': _('Радиус в километрах для уведомлений о потерянных животных поблизости'),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Проверяем, что хотя бы один тип уведомлений включен
        if not cleaned_data.get('email_enabled') and not cleaned_data.get('push_enabled'):
            raise forms.ValidationError(
                _('Необходимо включить хотя бы один тип уведомлений (email или push)')
            )
        
        # Проверяем корректность периода тишины
        quiet_start = cleaned_data.get('quiet_hours_start')
        quiet_end = cleaned_data.get('quiet_hours_end')
        if quiet_start and quiet_end and quiet_start >= quiet_end:
            raise forms.ValidationError(
                _('Время начала периода тишины должно быть меньше времени окончания')
            )
        
        # Проверяем радиус для уведомлений о потерянных животных
        radius = cleaned_data.get('notify_lost_pets_radius')
        if radius is not None and radius < 0:
            raise forms.ValidationError(
                _('Радиус не может быть отрицательным')
            )
        
        return cleaned_data 