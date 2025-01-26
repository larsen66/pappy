from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import (
    UserProfile,
    SellerProfile,
    SpecialistProfile,
    VerificationDocument,
    Review
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'created_at')
    search_fields = ('user__phone', 'location')
    list_filter = ('created_at',)

@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'seller_type', 'company_name', 'is_verified', 'rating')
    list_filter = ('seller_type', 'is_verified')
    search_fields = ('user__phone', 'company_name', 'inn')

@admin.register(SpecialistProfile)
class SpecialistProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'experience_years', 'is_verified', 'rating')
    list_filter = ('specialization', 'is_verified')
    search_fields = ('user__phone', 'services')

@admin.register(VerificationDocument)
class VerificationDocumentAdmin(admin.ModelAdmin):
    list_display = ['user', 'document_type', 'status', 'created_at']
    list_filter = ['status', 'document_type', 'created_at']
    search_fields = ['user__phone', 'document_type']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['author', 'seller', 'specialist', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['author__phone', 'comment'] 