from django.urls import path
from . import views

app_name = 'kotopsinder'

urlpatterns = [
    path('', views.swipe_view, name='swipe'),
    path('api/swipe/', views.record_swipe, name='record_swipe'),
    path('api/undo/', views.undo_last_swipe, name='undo_swipe'),
    path('api/next-cards/', views.get_next_cards, name='next_cards'),
] 