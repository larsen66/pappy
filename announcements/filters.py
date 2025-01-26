from django_filters import rest_framework as filters
from .models import Announcement

class AnnouncementFilter(filters.FilterSet):
    min_price = filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = filters.NumberFilter(field_name='price', lookup_expr='lte')
    location = filters.CharFilter(field_name='location', lookup_expr='icontains')
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = Announcement
        fields = {
            'category': ['exact'],
            'type': ['exact'],
            'status': ['exact'],
            'is_premium': ['exact'],
            'author': ['exact'],
        } 