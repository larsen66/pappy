from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('dialogs/', views.dialogs_list, name='dialogs_list'),
    path('dialogs/<int:dialog_id>/', views.dialog_detail, name='dialog_detail'),
    path('dialogs/<int:dialog_id>/send/', views.send_message, name='send_message'),
    path('dialogs/<int:dialog_id>/new/', views.get_new_messages, name='get_new_messages'),
    path('dialogs/create/<int:product_id>/', views.create_dialog, name='create_dialog'),
] 