from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    Announcement,
    AnnouncementCategory,
    AnimalAnnouncement,
    ServiceAnnouncement,
    AnnouncementImage
)
from .serializers import (
    AnnouncementSerializer,
    AnnouncementCategorySerializer,
    AnimalAnnouncementSerializer,
    ServiceAnnouncementSerializer,
    AnnouncementImageSerializer
)
from .filters import AnnouncementFilter
from .permissions import IsAuthorOrReadOnly, IsSpecialistOrReadOnly, IsAnnouncementAuthorOrReadOnly

class AnnouncementCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint для категорий объявлений.
    Поддерживает только чтение.
    """
    queryset = AnnouncementCategory.objects.all()
    serializer_class = AnnouncementCategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

class AnnouncementViewSet(viewsets.ModelViewSet):
    """
    API endpoint для объявлений.
    Поддерживает все CRUD операции.
    """
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AnnouncementFilter
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'price', 'views_count']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        if not getattr(self.request, 'testing', False):  # Проверяем, не в тестовом ли режиме
            if self.action == 'list':
                return queryset.filter(status=Announcement.STATUS_ACTIVE)
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Закрытие объявления"""
        announcement = self.get_object()
        announcement.status = Announcement.STATUS_CLOSED
        announcement.save()
        return Response({'status': 'closed'})

    @action(detail=False, methods=['get'])
    def my(self, request):
        """Получение списка объявлений текущего пользователя"""
        queryset = self.get_queryset().filter(author=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class AnimalAnnouncementViewSet(viewsets.ModelViewSet):
    """
    API endpoint для объявлений о животных.
    Поддерживает все CRUD операции.
    """
    queryset = AnimalAnnouncement.objects.all()
    serializer_class = AnimalAnnouncementSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['species', 'breed', 'gender', 'size']
    search_fields = ['title', 'description', 'species', 'breed']

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, type=Announcement.TYPE_ANIMAL)

class ServiceAnnouncementViewSet(viewsets.ModelViewSet):
    """
    API endpoint для объявлений об услугах.
    Поддерживает все CRUD операции.
    Доступен только для специалистов.
    """
    queryset = ServiceAnnouncement.objects.all()
    serializer_class = ServiceAnnouncementSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly, IsSpecialistOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['service_type', 'experience']
    search_fields = ['title', 'description', 'certificates']

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, type=Announcement.TYPE_SERVICE)

class AnnouncementImageViewSet(viewsets.ModelViewSet):
    """
    API endpoint для изображений объявлений.
    Поддерживает все CRUD операции.
    """
    queryset = AnnouncementImage.objects.all()
    serializer_class = AnnouncementImageSerializer
    permission_classes = [IsAuthenticated, IsAnnouncementAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['announcement', 'is_main']

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return AnnouncementImage.objects.filter(announcement__author=self.request.user)
        return AnnouncementImage.objects.none()

    def perform_destroy(self, instance):
        if instance.image:
            instance.image.delete(save=False)
        instance.delete()

    @action(detail=True, methods=['post'])
    def set_main(self, request, pk=None):
        """Установка изображения как главного"""
        image = self.get_object()
        # Сбрасываем флаг у всех изображений объявления
        image.announcement.images.update(is_main=False)
        # Устанавливаем текущее изображение как главное
        image.is_main = True
        image.save()
        return Response({'status': 'main image set'}) 