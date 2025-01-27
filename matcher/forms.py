from django import forms
from django.utils.translation import gettext_lazy as _
from .models import UserPreferences
from announcements.models import AnimalAnnouncement

class UserPreferencesForm(forms.ModelForm):
    """Форма для настройки предпочтений пользователя"""
    
    class Meta:
        model = UserPreferences
        fields = [
            'preferred_species', 'preferred_breeds',
            'preferred_age_min', 'preferred_age_max',
            'preferred_gender', 'size_preference',
            'color_preference', 'requires_pedigree',
            'requires_vaccinated', 'requires_passport',
            'max_distance'
        ]
        widgets = {
            'preferred_species': forms.SelectMultiple(attrs={
                'class': 'select2',
                'data-placeholder': _('Выберите виды животных')
            }),
            'preferred_breeds': forms.SelectMultiple(attrs={
                'class': 'select2',
                'data-placeholder': _('Выберите породы')
            }),
            'size_preference': forms.SelectMultiple(attrs={
                'class': 'select2',
                'data-placeholder': _('Выберите размеры')
            }),
            'color_preference': forms.SelectMultiple(attrs={
                'class': 'select2',
                'data-placeholder': _('Выберите окрасы')
            }),
            'preferred_gender': forms.Select(attrs={
                'class': 'form-select'
            }),
            'preferred_age_min': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '30'
            }),
            'preferred_age_max': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '30'
            }),
            'max_distance': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '500'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Получаем уникальные значения из базы
        species_choices = AnimalAnnouncement.objects.values_list(
            'species', flat=True
        ).distinct()
        breed_choices = AnimalAnnouncement.objects.values_list(
            'breed', flat=True
        ).distinct()
        
        # Обновляем choices для полей
        self.fields['preferred_species'].choices = [
            (species, species) for species in species_choices
        ]
        self.fields['preferred_breeds'].choices = [
            (breed, breed) for breed in breed_choices
        ]
        self.fields['size_preference'].choices = AnimalAnnouncement.SIZE_CHOICES
        
        # Добавляем подсказки
        self.fields['max_distance'].help_text = _(
            'Максимальное расстояние для поиска в километрах'
        )
        self.fields['requires_pedigree'].help_text = _(
            'Показывать только животных с родословной'
        )
        self.fields['requires_vaccinated'].help_text = _(
            'Показывать только вакцинированных животных'
        )
    
    def clean(self):
        cleaned_data = super().clean()
        min_age = cleaned_data.get('preferred_age_min')
        max_age = cleaned_data.get('preferred_age_max')
        
        if min_age and max_age and min_age > max_age:
            raise forms.ValidationError(_(
                'Минимальный возраст не может быть больше максимального'
            ))
        
        return cleaned_data 