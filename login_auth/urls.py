from django.urls import path
from . import views

app_name = 'login_auth'

urlpatterns = [
    path('', views.phone_login_view, name='phone_login'),
    path('verify/', views.verify_sms_view, name='verify_sms'),
    path('resend/', views.resend_code_view, name='resend_code'),
    path('gosuslugi/', views.gosuslugi_view, name='gosuslugi'),
    path('logout/', views.logout_view, name='logout'),
] 