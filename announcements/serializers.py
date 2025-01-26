from rest_framework import serializers
from .models import (
    Announcement,
    AnnouncementCategory,
    AnimalAnnouncement,
    ServiceAnnouncement,
    AnnouncementImage
)

class AnnouncementCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AnnouncementCategory
        fields = ['id', 'name', 'slug', 'parent']

class AnnouncementImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnnouncementImage
        fields = ['id', 'announcement', 'image', 'is_main', 'created_at']
        read_only_fields = ['created_at']

class AnnouncementSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    images = AnnouncementImageSerializer(many=True, read_only=True)
    main_image = serializers.SerializerMethodField()

    class Meta:
        model = Announcement
        fields = [
            'id', 'title', 'description', 'price', 'category', 'category_name',
            'type', 'status', 'author', 'author_name', 'location', 'latitude',
            'longitude', 'created_at', 'updated_at', 'views_count', 'is_premium',
            'images', 'main_image'
        ]
        read_only_fields = [
            'author', 'created_at', 'updated_at', 'views_count', 'is_premium'
        ]

    def get_main_image(self, obj):
        main_image = obj.images.filter(is_main=True).first()
        if main_image:
            return AnnouncementImageSerializer(main_image).data
        return None

    def validate_price(self, value):
        if value and value < 0:
            raise serializers.ValidationError("Цена не может быть отрицательной")
        return value

class AnimalAnnouncementSerializer(AnnouncementSerializer):
    class Meta(AnnouncementSerializer.Meta):
        model = AnimalAnnouncement
        fields = AnnouncementSerializer.Meta.fields + [
            'species', 'breed', 'age', 'gender', 'size', 'color',
            'pedigree', 'vaccinated', 'passport', 'microchipped'
        ]

    def validate_age(self, value):
        if value and value < 0:
            raise serializers.ValidationError("Возраст не может быть отрицательным")
        return value

class ServiceAnnouncementSerializer(AnnouncementSerializer):
    class Meta(AnnouncementSerializer.Meta):
        model = ServiceAnnouncement
        fields = AnnouncementSerializer.Meta.fields + [
            'service_type', 'experience', 'certificates', 'schedule'
        ]

    def validate_experience(self, value):
        if value and value < 0:
            raise serializers.ValidationError("Опыт работы не может быть отрицательным")
        return value

    def validate(self, data):
        data = super().validate(data)
        user = self.context['request'].user if 'request' in self.context else None
        
        if user and not user.is_specialist and self.instance is None:
            raise serializers.ValidationError({
                "non_field_errors": ["Только специалисты могут создавать объявления об услугах"]
            })
        
        return data 