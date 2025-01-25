from django import forms
from django.utils.translation import gettext_lazy as _
from .models import (
    Announcement,
    AnnouncementCategory,
    AnimalAnnouncement,
    ServiceAnnouncement,
    MatingAnnouncement,
    LostFoundAnnouncement,
    AnnouncementImage
)

class AnnouncementForm(forms.ModelForm):
    """Base form for all announcements"""
    class Meta:
        model = Announcement
        fields = ['title', 'description', 'category', 'price', 'location', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }

class AnimalAnnouncementForm(AnnouncementForm):
    class Meta(AnnouncementForm.Meta):
        model = AnimalAnnouncement
        fields = AnnouncementForm.Meta.fields + [
            'species', 'breed', 'age', 'gender', 'size', 'color',
            'pedigree', 'vaccinated', 'passport', 'microchipped'
        ]

class ServiceAnnouncementForm(AnnouncementForm):
    class Meta(AnnouncementForm.Meta):
        model = ServiceAnnouncement
        fields = AnnouncementForm.Meta.fields + [
            'service_type', 'experience', 'certificates', 'schedule'
        ]
        widgets = {
            **AnnouncementForm.Meta.widgets,
            'certificates': forms.Textarea(attrs={'rows': 3}),
            'schedule': forms.Textarea(attrs={'rows': 3}),
        }

class MatingAnnouncementForm(AnnouncementForm):
    """Form for mating announcements"""
    class Meta(AnnouncementForm.Meta):
        model = MatingAnnouncement
        fields = AnnouncementForm.Meta.fields + ['requirements', 'achievements']
        widgets = {
            **AnnouncementForm.Meta.widgets,
            'requirements': forms.Textarea(attrs={'rows': 3}),
            'achievements': forms.Textarea(attrs={'rows': 3}),
        }

class LostFoundAnnouncementForm(AnnouncementForm):
    class Meta(AnnouncementForm.Meta):
        model = LostFoundAnnouncement
        fields = AnnouncementForm.Meta.fields + ['type', 'date_lost_found', 'distinctive_features']
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