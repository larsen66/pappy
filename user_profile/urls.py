from django.urls import path
from . import views

app_name = 'user_profile'

urlpatterns = [
    path('onboarding/', views.onboarding_view, name='onboarding'),
    path('settings/', views.profile_settings, name='settings'),
    path('seller/', views.seller_profile, name='seller_profile'),
    path('specialist/', views.specialist_profile, name='specialist_profile'),
    path('verification/request/', views.verification_request, name='verification_request'),
    path('verification/status/', views.verification_status, name='verification_status'),
    path('verification/pending/', views.verification_pending, name='verification_pending'),
    path('public/<int:user_id>/', views.public_profile, name='public_profile'),
    path('seller/create/', views.create_seller_profile, name='create_seller_profile'),
    path('seller/update/<int:pk>/', views.update_seller_profile, name='update_seller_profile'),
    path('seller/delete/', views.delete_profile, name='delete'),
    path('specialist/create/', views.create_specialist_profile, name='create_specialist_profile'),
    path('specialist/update/<int:pk>/', views.update_specialist_profile, name='update_specialist_profile'),
    path('specialists/', views.specialist_list, name='specialist_list'),
    path('specialists/<int:pk>/', views.specialist_detail, name='specialist_detail'),
    path('become-seller/', views.become_seller, name='become_seller'),
    path('become-specialist/', views.become_specialist, name='become_specialist'),
] 