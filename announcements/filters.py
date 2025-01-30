import django_filters
from django.db.models import Q
from .models import Announcement
from math import radians, sin, cos, sqrt, atan2

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # радиус Земли в километрах

    lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return distance

class AnnouncementFilter(django_filters.FilterSet):
    # Фильтры по цене
    price__gte = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price__lte = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    
    # Фильтры по дате
    created_at__gte = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at__lte = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    # Фильтры для животных
    animal_species = django_filters.CharFilter(field_name='animal_details__species')
    animal_breed = django_filters.CharFilter(field_name='animal_details__breed')
    animal_age__gte = django_filters.NumberFilter(field_name='animal_details__age', lookup_expr='gte')
    animal_age__lte = django_filters.NumberFilter(field_name='animal_details__age', lookup_expr='lte')
    
    # Фильтры для услуг
    service_type = django_filters.CharFilter(field_name='service_details__service_type')
    service_experience__gte = django_filters.NumberFilter(field_name='service_details__experience', lookup_expr='gte')
    
    # Полнотекстовый поиск
    search = django_filters.CharFilter(method='filter_search')
    
    # Фильтр по местоположению
    location = django_filters.CharFilter(method='filter_location')
    
    class Meta:
        model = Announcement
        fields = {
            'category': ['exact'],
            'type': ['exact'],
            'status': ['exact'],
            'is_premium': ['exact'],
            'author': ['exact'],
            'is_active': ['exact'],
        }
    
    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
            
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(animal_details__breed__icontains=value) |
            Q(service_details__service_type__icontains=value)
        )
    
    def filter_location(self, queryset, name, value):
        if not value:
            return queryset
            
        return queryset.filter(
            Q(address__icontains=value) |
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

    def filter_distance(self, queryset, name, value):
        lat = self.data.get('latitude')
        lon = self.data.get('longitude')
        
        if not (lat and lon and value):
            return queryset
            
        filtered_announcements = []
        for announcement in queryset:
            if announcement.latitude and announcement.longitude:
                distance = calculate_distance(
                    float(lat), float(lon),
                    float(announcement.latitude), float(announcement.longitude)
                )
                if distance <= float(value):
                    filtered_announcements.append(announcement.id)
        
        return queryset.filter(id__in=filtered_announcements)

    def filter_latitude(self, queryset, name, value):
        # Implementation of filter_latitude method
        pass

    def filter_longitude(self, queryset, name, value):
        # Implementation of filter_longitude method
        pass 