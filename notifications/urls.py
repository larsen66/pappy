from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='list'),
    path('preferences/', views.notification_preferences, name='preferences'),
    path('mark-as-read/', views.mark_as_read, name='mark_as_read'),
    path('register-push-token/', views.register_push_token, name='register_push_token'),
    path('unregister-push-token/', views.unregister_push_token, name='unregister_push_token'),
    path('<int:pk>/', views.notification_detail, name='detail'),
    path('mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('unread-count/', views.get_unread_count, name='unread_count'),
    path('delete/<int:notification_id>/', views.delete_notification, name='delete'),
] 