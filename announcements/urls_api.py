from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_api import (
    AnnouncementViewSet,
    AnnouncementCategoryViewSet,
    AnimalAnnouncementViewSet,
    ServiceAnnouncementViewSet,
    AnnouncementImageViewSet
)

app_name = 'api'

router = DefaultRouter()
router.register(r'announcements', AnnouncementViewSet)
router.register(r'categories', AnnouncementCategoryViewSet)
router.register(r'animal-announcements', AnimalAnnouncementViewSet)
router.register(r'service-announcements', ServiceAnnouncementViewSet)
router.register(r'images', AnnouncementImageViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 