from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model, authenticate
from django.db.models import Q
from ..models import UserProfile, SellerProfile, SpecialistProfile, VerificationDocument
from ..serializers import (
    UserProfileSerializer, SellerProfileSerializer, 
    SpecialistProfileSerializer, VerificationDocumentSerializer
)
from .utils import get_token_for_user

User = get_user_model()

@api_view(['GET'])
def profile_list(request):
    if not request.user.is_authenticated:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    profiles = UserProfile.objects.all()
    serializer = UserProfileSerializer(profiles, many=True)
    return Response(serializer.data)

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile_detail(request, pk):
    profile = get_object_or_404(UserProfile, pk=pk)
    if request.method == 'GET':
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    elif request.method == 'PATCH':
        if profile.user != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def seller_profile_create(request):
    serializer = SellerProfileSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def seller_profile_detail(request, pk):
    profile = get_object_or_404(SellerProfile, user_id=pk)
    if request.method == 'GET':
        serializer = SellerProfileSerializer(profile)
        return Response(serializer.data)
    elif request.method == 'PATCH':
        if profile.user != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = SellerProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def specialist_profile_create(request):
    serializer = SpecialistProfileSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def specialist_profile_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    # Создаем профиль специалиста, если его нет
    profile, created = SpecialistProfile.objects.get_or_create(
        user=user,
        defaults={
            'specialization': 'veterinarian',
            'experience_years': 0,
            'services': '',
            'price_range': '0-0'
        }
    )
    
    if request.method == 'GET':
        serializer = SpecialistProfileSerializer(profile)
        return Response(serializer.data)
    elif request.method == 'PATCH':
        if profile.user != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = SpecialistProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def specialist_search(request):
    queryset = SpecialistProfile.objects.all()
    
    specialization = request.query_params.get('specialization')
    if specialization:
        queryset = queryset.filter(specialization=specialization)
    
    min_experience = request.query_params.get('min_experience')
    if min_experience:
        queryset = queryset.filter(experience_years__gte=min_experience)
    
    min_rating = request.query_params.get('min_rating')
    if min_rating:
        queryset = queryset.filter(rating__gte=min_rating)
    
    serializer = SpecialistProfileSerializer(queryset, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_document(request):
    serializer = VerificationDocumentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def profile_upload_image(request):
    """
    Upload profile image
    """
    if 'image' not in request.FILES:
        return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)
        
    image = request.FILES['image']
    profile = request.user.profile
    profile.avatar = image
    profile.save()
    
    # Проверяем, что изображение было успешно сохранено
    if profile.avatar and hasattr(profile.avatar, 'url'):
        return Response({'image_url': profile.avatar.url})
    return Response({'image_url': None})

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_user_list(request):
    users = User.objects.all()
    serializer = UserProfileSerializer(users, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def token_obtain(request):
    phone = request.data.get('phone')
    password = request.data.get('password')
    
    user = authenticate(phone=phone, password=password)
    if user:
        token = get_token_for_user(user)
        return Response({'access': token})
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED) 