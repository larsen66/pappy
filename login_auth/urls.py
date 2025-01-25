from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'login_auth'

urlpatterns = [
    path('login/', views.login, name='login'),
    path('sms-validation/', views.sms_validation, name='sms_validation'),
    path('signup/', views.signup, name='signup'),
    path('signup-success/', views.signup_success, name='signup_success'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('send-code/', views.send_code, name='send_code'),
    path('verify-code/', views.verify_code, name='verify_code'),
] 