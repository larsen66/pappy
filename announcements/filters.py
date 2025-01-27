from django_filters import rest_framework as filters
from django.db.models import Q
from .models import Announcement
from django.contrib.gis.geos import Point, D

class AnnouncementFilter(filters.FilterSet):
    # Расширенные фильтры по цене
    min_price = filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = filters.NumberFilter(field_name='price', lookup_expr='lte')
    
    # Расширенные фильтры по местоположению
    location = filters.CharFilter(method='filter_location')
    radius = filters.NumberFilter(method='filter_radius')
    
    # Фильтры по дате
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    # Полнотекстовый поиск
    search = filters.CharFilter(method='filter_search')
    
    # Фильтры для животных
    species = filters.CharFilter(field_name='animalannouncement__species')
    breed = filters.CharFilter(field_name='animalannouncement__breed')
    age_min = filters.NumberFilter(field_name='animalannouncement__age', lookup_expr='gte')
    age_max = filters.NumberFilter(field_name='animalannouncement__age', lookup_expr='lte')
    
    # Фильтры для услуг
    service_type = filters.CharFilter(field_name='serviceannouncement__service_type')
    experience = filters.NumberFilter(field_name='serviceannouncement__experience', lookup_expr='gte')
    
    class Meta:
        model = Announcement
        fields = {
            'category': ['exact'],
            'type': ['exact'],
            'status': ['exact'],
            'is_premium': ['exact'],
            'author': ['exact'],
        }
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(animalannouncement__breed__icontains=value) |
            Q(serviceannouncement__service_type__icontains=value)
        )
    
    def filter_location(self, queryset, name, value):
        return queryset.filter(
            Q(location__icontains=value) |
            Q(author__profile__city__icontains=value)
        )
    
    def filter_radius(self, queryset, name, value):
        # Если у нас есть координаты в запросе
        lat = self.data.get('latitude')
        lon = self.data.get('longitude')
        if lat and lon and value:
            return queryset.filter(
                location__distance_lte=(Point(float(lon), float(lat)), D(km=value))
            )
        return queryset 