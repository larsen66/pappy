from rest_framework import serializers
from .models import UserProfile, SellerProfile, SpecialistProfile, VerificationDocument

class UserProfileSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source='user.phone', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'phone', 'bio', 'location', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class SellerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerProfile
        fields = ['seller_type', 'company_name', 'inn', 'description', 'website']
        read_only_fields = ['is_verified', 'rating']

class SpecialistProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecialistProfile
        fields = ['specialization', 'experience_years', 'services', 'price_range', 'certificates']
        read_only_fields = ['is_verified', 'rating']

class VerificationDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationDocument
        fields = ['document', 'comment']
        read_only_fields = ['is_verified', 'uploaded_at'] 