from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('profiles/', views.profile_list, name='profile-list'),
    path('profiles/<int:pk>/', views.profile_detail, name='profile-detail'),
    path('seller-profiles/<int:pk>/', views.seller_profile_detail, name='seller-profile-detail'),
    path('specialist-profiles/<int:pk>/', views.specialist_profile_detail, name='specialist-profile-detail'),
    path('specialists/search/', views.specialist_search, name='specialist-search'),
    path('profile/upload-image/', views.profile_upload_image, name='profile-upload-image'),
    path('admin/users/', views.admin_user_list, name='admin-user-list'),
    path('token/', views.token_obtain, name='token_obtain'),
] 