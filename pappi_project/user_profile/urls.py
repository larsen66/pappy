from django.urls import path
from . import views

app_name = 'user_profile'

urlpatterns = [
    path('', views.profile_view, name='profile'),
    path('onboarding/', views.onboarding_view, name='onboarding'),
    path('settings/', views.settings_view, name='settings'),
    path('seller/', views.seller_profile_view, name='seller_profile'),
] 