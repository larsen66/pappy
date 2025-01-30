from django import forms
from django.utils.translation import gettext_lazy as _
from .models import (
    Announcement,
    AnnouncementCategory,
    AnimalAnnouncement,
    ServiceAnnouncement,
    MatingAnnouncement,
    LostFoundAnnouncement,
    AnnouncementImage,
    LostPet
)

class AnnouncementForm(forms.ModelForm):
    """Base form for all announcements"""
    latitude = forms.DecimalField(max_digits=9, decimal_places=6, required=False)
    longitude = forms.DecimalField(max_digits=9, decimal_places=6, required=False)
    address = forms.CharField(max_length=255, required=False)

    class Meta:
        model = Announcement
        fields = ['title', 'description', 'category', 'type', 'price', 'address', 'latitude', 'longitude', 'images']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get('latitude')
        longitude = cleaned_data.get('longitude')

        if (latitude and not longitude) or (longitude and not latitude):
            raise forms.ValidationError('Необходимо указать обе координаты')

        return cleaned_data

class AnimalAnnouncementForm(forms.ModelForm):
    class Meta:
        model = AnimalAnnouncement
        fields = [
            'species', 'breed', 'age', 'gender', 'size', 'color',
            'pedigree', 'vaccinated', 'passport', 'microchipped'
        ]
        widgets = {
            'age': forms.NumberInput(attrs={'min': 0}),
        }

class ServiceAnnouncementForm(forms.ModelForm):
    class Meta:
        model = ServiceAnnouncement
        fields = ['service_type', 'experience', 'certificates', 'schedule']
        widgets = {
            'certificates': forms.Textarea(attrs={'rows': 3}),
            'schedule': forms.Textarea(attrs={'rows': 3}),
        }

class MatingAnnouncementForm(forms.ModelForm):
    """Form for mating announcements with medical documents and requirements"""
    
    class Meta:
        model = MatingAnnouncement
        fields = [
            'animal',
            'has_medical_exam', 'medical_exam_date', 'vaccinations',
            'genetic_tests', 'medical_documents',
            'titles', 'achievements', 'show_participation',
            'partner_requirements', 'preferred_breeds',
            'min_partner_age', 'max_partner_age',
            'required_medical_tests', 'required_titles',
            'mating_conditions', 'price_policy', 'contract_required'
        ]
        widgets = {
            'medical_exam_date': forms.DateInput(attrs={'type': 'date'}),
            'vaccinations': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Введите в формате JSON'}),
            'genetic_tests': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Введите в формате JSON'}),
            'titles': forms.TextInput(attrs={'placeholder': 'Введите титулы через запятую'}),
            'achievements': forms.Textarea(attrs={'rows': 3}),
            'show_participation': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Введите в формате JSON'}),
            'partner_requirements': forms.Textarea(attrs={'rows': 3}),
            'preferred_breeds': forms.TextInput(attrs={'placeholder': 'Введите породы через запятую'}),
            'required_medical_tests': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Введите в формате JSON'}),
            'required_titles': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Введите в формате JSON'}),
            'mating_conditions': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Проверка возраста партнера
        min_age = cleaned_data.get('min_partner_age')
        max_age = cleaned_data.get('max_partner_age')
        if min_age and max_age and min_age > max_age:
            raise forms.ValidationError(_('Минимальный возраст не может быть больше максимального'))
        
        # Проверка даты медосмотра
        medical_exam = cleaned_data.get('has_medical_exam')
        exam_date = cleaned_data.get('medical_exam_date')
        if medical_exam and not exam_date:
            raise forms.ValidationError(_('Укажите дату медосмотра'))
        
        return cleaned_data
    
    def clean_medical_documents(self):
        documents = self.cleaned_data.get('medical_documents')
        if documents:
            if documents.size > 10 * 1024 * 1024:  # 10MB limit
                raise forms.ValidationError(_('Размер файла не должен превышать 10MB'))
            if not documents.name.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                raise forms.ValidationError(_('Поддерживаются только файлы PDF, JPG и PNG'))
        return documents

class LostFoundAnnouncementForm(forms.ModelForm):
    class Meta:
        model = LostFoundAnnouncement
        fields = ['type', 'date_lost_found', 'distinctive_features']
        widgets = {
            'date_lost_found': forms.DateInput(attrs={'type': 'date'}),
            'distinctive_features': forms.Textarea(attrs={'rows': 3}),
        }

class AnnouncementImageForm(forms.ModelForm):
    """Form for announcement images"""
    class Meta:
        model = AnnouncementImage
        fields = ['image', 'is_main']

class AnnouncementSearchForm(forms.Form):
    query = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': _('Поиск по объявлениям...'),
        'class': 'form-control'
    }))
    category = forms.ModelChoiceField(
        queryset=AnnouncementCategory.objects.all(),
        required=False,
        empty_label=_('Все категории')
    )
    type = forms.ChoiceField(
        choices=[('', _('Все типы'))] + Announcement._meta.get_field('type').choices,
        required=False
    )
    min_price = forms.DecimalField(required=False, min_value=0)
    max_price = forms.DecimalField(required=False, min_value=0)
    location = forms.CharField(required=False)
    
    def clean(self):
        cleaned_data = super().clean()
        min_price = cleaned_data.get('min_price')
        max_price = cleaned_data.get('max_price')
        
        if min_price and max_price and min_price > max_price:
            raise forms.ValidationError(_('Минимальная цена не может быть больше максимальной'))
        
        return cleaned_data

class LostPetForm(forms.ModelForm):
    latitude = forms.FloatField(widget=forms.HiddenInput())
    longitude = forms.FloatField(widget=forms.HiddenInput())
    
    class Meta:
        model = LostPet
        fields = [
            'status', 'date_lost_found', 'pet_type', 'breed', 'color',
            'age', 'distinctive_features', 'has_collar', 'has_chip',
            'chip_number', 'last_seen_location', 'search_radius',
            'contact_name', 'contact_phone', 'contact_email', 'reward_offered'
        ]
        widgets = {
            'date_lost_found': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'distinctive_features': forms.Textarea(attrs={'rows': 3}),
            'search_radius': forms.NumberInput(attrs={'min': 1, 'max': 50}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        lat = cleaned_data.get('latitude')
        lon = cleaned_data.get('longitude')
        
        if lat and lon:
            cleaned_data['last_seen_location'] = (lon, lat)
        else:
            raise forms.ValidationError(_('Необходимо указать местоположение на карте'))
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.last_seen_location = (
            self.cleaned_data['longitude'],
            self.cleaned_data['latitude']
        )
        if commit:
            instance.save()
        return instance 