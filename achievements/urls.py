from django.urls import path
from . import views

app_name = 'achievements'

urlpatterns = [
    path('achievements/', views.achievements_list, name='achievements_list'),
    path('achievements/<int:achievement_id>/', views.achievement_detail, name='achievement_detail'),
    path('badges/', views.badges_list, name='badges_list'),
    path('badges/<int:badge_id>/', views.badge_detail, name='badge_detail'),
] 