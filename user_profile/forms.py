from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from .models import UserProfile, SellerProfile, SpecialistProfile, VerificationDocument

User = get_user_model()

def validate_inn(value):
    if not value.isdigit():
        raise ValidationError(_('ИНН должен содержать только цифры'))
    if len(value) not in [10, 12]:
        raise ValidationError(_('ИНН должен содержать 10 или 12 цифр'))

class UserSettingsForm(forms.ModelForm):
    """Форма основных настроек пользователя"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        exclude = ['is_verified', 'is_seller', 'is_specialist', 'is_shelter']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Имя')}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Фамилия')}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Email')})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

class UserProfileForm(forms.ModelForm):
    """Форма профиля пользователя"""
    class Meta:
        model = UserProfile
        fields = ['avatar', 'bio', 'location']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Расскажите о себе')
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ваше местоположение')
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control'
            })
        }

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            if avatar.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError(_('Размер файла не должен превышать 5MB'))
            return avatar
        return None

class SellerProfileForm(forms.ModelForm):
    """Форма для редактирования профиля продавца"""
    inn = forms.CharField(
        max_length=12,
        validators=[validate_inn],
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = SellerProfile
        fields = ['seller_type', 'company_name', 'inn', 'description', 'website']
        widgets = {
            'seller_type': forms.Select(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company_name'].required = False
        self.fields['website'].required = False

    def clean(self):
        cleaned_data = super().clean()
        seller_type = cleaned_data.get('seller_type')
        inn = cleaned_data.get('inn')
        company_name = cleaned_data.get('company_name')

        if seller_type in ['entrepreneur', 'company']:
            if not inn:
                self.add_error('inn', _('ИНН обязателен для ИП и компаний'))
            if not company_name:
                self.add_error('company_name', _('Название компании обязательно для ИП и компаний'))

        return cleaned_data

class SpecialistProfileForm(forms.ModelForm):
    """Форма для редактирования профиля специалиста"""
    certificates = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = SpecialistProfile
        fields = ['specialization', 'experience_years', 'services', 'price_range', 'certificates']
        widgets = {
            'specialization': forms.Select(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'services': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'price_range': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_certificates(self):
        certificates = self.cleaned_data.get('certificates')
        if certificates:
            # Проверка размера и типа файлов может быть добавлена здесь
            return certificates
        return None

class VerificationDocumentForm(forms.ModelForm):
    class Meta:
        model = VerificationDocument
        fields = ['document', 'document_type', 'comment']
        widgets = {
            'document': forms.FileInput(attrs={'class': 'form-control'}),
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
        help_texts = {
            'document': _('Загрузите документ, подтверждающий ваш статус'),
            'comment': _('Дополнительная информация о вашем статусе'),
        }

class SellerVerificationForm(forms.ModelForm):
    """Форма для подачи заявки на верификацию продавца"""
    inn = forms.CharField(
        max_length=12,
        validators=[validate_inn],
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = SellerProfile
        fields = ['seller_type', 'company_name', 'inn']
        widgets = {
            'seller_type': forms.Select(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.seller_type in ['entrepreneur', 'company']:
            self.fields['company_name'].required = True
            self.fields['inn'].required = True

class SpecialistVerificationForm(forms.ModelForm):
    """Форма для подачи заявки на верификацию специалиста"""
    certificates = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        required=True
    )

    class Meta:
        model = SpecialistProfile
        fields = ['specialization', 'experience_years', 'services', 'certificates']
        widgets = {
            'specialization': forms.Select(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'services': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class VerificationRequestForm(forms.Form):
    document = forms.FileField(
        label=_('Документ'),
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        help_text=_('Загрузите документ, подтверждающий ваш статус')
    )
    document_type = forms.ChoiceField(
        label=_('Тип документа'),
        choices=VerificationDocument.DOCUMENT_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    comment = forms.CharField(
        label=_('Комментарий'),
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        required=False,
        help_text=_('Дополнительная информация о вашем статусе')
    ) 