from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from .forms import (
    UserSettingsForm, UserProfileForm, SellerProfileForm, SpecialistProfileForm,
    VerificationDocumentForm, VerificationRequestForm,
    SellerVerificationForm, SpecialistVerificationForm
)
from .models import (
    SellerProfile, SpecialistProfile, VerificationDocument
)
from notifications.models import Notification
import logging

logger = logging.getLogger(__name__)
console_logger = logging.getLogger('console')

@login_required
def profile_settings(request):
    """Страница настроек профиля пользователя"""
    try:
        if request.method == 'POST':
            user_form = UserSettingsForm(request.POST, instance=request.user)
            profile_form = UserProfileForm(
                request.POST,
                request.FILES,
                instance=request.user.userprofile
            )
            
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, _('Профиль успешно обновлен'))
                return redirect('user_profile:settings')
        else:
            user_form = UserSettingsForm(instance=request.user)
            profile_form = UserProfileForm(instance=request.user.userprofile)
        
        return render(request, 'user_profile/settings.html', {
            'user_form': user_form,
            'profile_form': profile_form,
            'user': request.user,
            'profile': request.user.userprofile
        })
    except Exception as e:
        logger.error(f"Error in profile settings: {str(e)}", exc_info=True)
        messages.error(request, _('Произошла ошибка при загрузке профиля'))
        return redirect('user_profile:settings')

@login_required
def onboarding_view(request):
    """Обработка онбординга нового пользователя"""
    if request.user.userprofile.is_onboarded:
        return redirect('user_profile:settings')
    
    if request.method == 'POST':
        try:
            # Обновляем основную информацию пользователя
            request.user.first_name = request.POST.get('first_name', '').strip()
            request.user.last_name = request.POST.get('last_name', '').strip()
            request.user.email = request.POST.get('email', '').strip()
            request.user.save()
            
            # Отмечаем, что пользователь прошел онбординг
            request.user.userprofile.is_onboarded = True
            request.user.userprofile.save()
            
            console_logger.info(f"User {request.user.phone} completed onboarding")
            messages.success(request, 'Профиль успешно обновлен!')
            
            return redirect('catalog:home')
            
        except Exception as e:
            console_logger.error(f"Error during onboarding for user {request.user.phone}: {str(e)}")
            messages.error(request, 'Произошла ошибка при сохранении профиля. Пожалуйста, попробуйте еще раз.')
    
    return render(request, 'user_profile/onboarding.html')

@login_required
def seller_profile(request):
    """Страница настроек профиля продавца"""
    try:
        profile = request.user.seller_profile
        if isinstance(profile, SpecialistProfile):
            return redirect('user_profile:specialist_profile')
    except SellerProfile.DoesNotExist:
        profile = None
    
    if request.method == 'POST':
        form = SellerProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, _('Профиль продавца успешно обновлен'))
            return redirect('user_profile:seller_profile')
    else:
        form = SellerProfileForm(instance=profile)
    
    return render(request, 'user_profile/seller_profile.html', {
        'form': form,
        'profile': profile
    })

@login_required
def specialist_profile(request):
    """Страница настроек профиля специалиста"""
    try:
        profile = request.user.specialist_profile
    except SpecialistProfile.DoesNotExist:
        profile = None
    
    if request.method == 'POST':
        form = SpecialistProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, _('Профиль специалиста успешно обновлен'))
            return redirect('user_profile:specialist_profile')
    else:
        form = SpecialistProfileForm(instance=profile)
    
    return render(request, 'user_profile/specialist_profile.html', {
        'form': form,
        'profile': profile
    })

@login_required
def verification_request(request):
    """Отправка запроса на верификацию"""
    if request.method == 'POST':
        form = VerificationDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.user = request.user
            document.save()
            messages.success(request, 'Документы успешно загружены и отправлены на проверку')
            return redirect('user_profile:verification_status')
    else:
        form = VerificationDocumentForm()
    
    return render(request, 'user_profile/verification_request.html', {
        'form': form
    })

@login_required
def verification_status(request):
    """Просмотр статуса верификации"""
    documents = request.user.verification_documents.all().order_by('-created_at')
    return render(request, 'user_profile/verification_status.html', {
        'documents': documents
    })

@login_required
def verification_pending(request):
    """Страница ожидания верификации"""
    latest_document = request.user.verification_documents.filter(
        status='pending'
    ).first()
    
    return render(request, 'user_profile/verification_pending.html', {
        'document': latest_document
    })

@login_required
def public_profile(request, user_id):
    """Публичная страница профиля пользователя"""
    user = get_object_or_404(get_user_model(), id=user_id)
    try:
        seller_profile = user.seller_profile
        is_specialist = isinstance(seller_profile, SpecialistProfile)
    except SellerProfile.DoesNotExist:
        seller_profile = None
        is_specialist = False
    
    return render(request, 'user_profile/public_profile.html', {
        'profile_user': user,
        'seller_profile': seller_profile,
        'is_specialist': is_specialist
    })

@login_required
def create_seller_profile(request):
    if hasattr(request.user, 'seller_profile'):
        return redirect('user_profile:seller_profile')
    
    if request.method == 'POST':
        form = SellerProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, 'Профиль продавца успешно создан')
            return redirect('user_profile:seller_profile')
    else:
        form = SellerProfileForm()
    
    return render(request, 'user_profile/seller_profile_form.html', {'form': form})

@login_required
def update_seller_profile(request, pk=None):
    if pk and pk != request.user.id:
        raise PermissionDenied
    
    profile = get_object_or_404(SellerProfile, user=request.user)
    if request.method == 'POST':
        form = SellerProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль продавца успешно обновлен')
            return redirect('user_profile:seller_profile')
    else:
        form = SellerProfileForm(instance=profile)
    
    return render(request, 'user_profile/seller_profile_form.html', {'form': form})

@login_required
def delete_profile(request):
    if request.method == 'POST':
        user = request.user
        user.delete()
        messages.success(request, 'Ваш профиль был успешно удален')
        return redirect('login_auth:phone_login')
    return render(request, 'user_profile/delete_confirmation.html')

@login_required
def upload_document(request):
    if request.method == 'POST':
        form = VerificationDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.user = request.user
            document.save()
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'errors': form.errors})
    return HttpResponseForbidden()

@login_required
def create_specialist_profile(request):
    if hasattr(request.user, 'specialist_profile'):
        return redirect('user_profile:specialist_profile')
    
    if request.method == 'POST':
        form = SpecialistProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, 'Профиль специалиста успешно создан')
            return redirect('user_profile:specialist_profile')
    else:
        form = SpecialistProfileForm()
    
    return render(request, 'user_profile/specialist_profile_form.html', {'form': form})

def specialist_list(request):
    specialists = SpecialistProfile.objects.filter(is_verified=True).select_related('user')
    return render(request, 'user_profile/specialist_list.html', {
        'specialists': specialists,
    })

def specialist_detail(request, pk):
    specialist = get_object_or_404(SpecialistProfile, pk=pk, is_verified=True)
    return render(request, 'user_profile/specialist_detail.html', {
        'specialist': specialist,
    })

@login_required
def become_seller(request):
    """View for handling seller registration process"""
    if hasattr(request.user, 'seller_verification'):
        if request.user.seller_verification.status == 'PE':
            messages.info(request, _('Your seller verification is pending review.'))
            return redirect('user_profile:verification_pending')
        elif request.user.seller_verification.status == 'AP':
            messages.success(request, _('You are already a verified seller.'))
            return redirect('user_profile:profile')
    
    if request.method == 'POST':
        form = SellerVerificationForm(request.POST, request.FILES)
        if form.is_valid():
            verification = form.save(commit=False)
            verification.user = request.user
            verification.save()
            messages.success(request, _('Your seller verification request has been submitted.'))
            return redirect('user_profile:verification_pending')
    else:
        form = SellerVerificationForm()
    
    return render(request, 'user_profile/become_seller.html', {'form': form})

@login_required
def update_specialist_profile(request, pk=None):
    """Обновление профиля специалиста"""
    if pk and pk != request.user.id:
        raise PermissionDenied
    
    profile = get_object_or_404(SpecialistProfile, user=request.user)
    if request.method == 'POST':
        form = SpecialistProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль специалиста успешно обновлен')
            return redirect('user_profile:specialist_profile')
    else:
        form = SpecialistProfileForm(instance=profile)
    
    return render(request, 'user_profile/specialist_profile_form.html', {'form': form})

@login_required
def become_specialist(request):
    """Страница для подачи заявки на статус специалиста"""
    if hasattr(request.user, 'specialist_verification'):
        if request.user.specialist_verification.status == 'PE':
            messages.info(request, _('Ваша заявка на верификацию находится на рассмотрении.'))
            return redirect('user_profile:verification_pending')
        elif request.user.specialist_verification.status == 'AP':
            messages.success(request, _('Вы уже являетесь верифицированным специалистом.'))
            return redirect('user_profile:profile')
    
    if request.method == 'POST':
        form = SpecialistVerificationForm(request.POST, request.FILES)
        if form.is_valid():
            verification = form.save(commit=False)
            verification.user = request.user
            verification.save()
            messages.success(request, _('Ваша заявка на верификацию отправлена.'))
            return redirect('user_profile:verification_pending')
    else:
        form = SpecialistVerificationForm()
    
    return render(request, 'user_profile/become_specialist.html', {'form': form})

@login_required
def profile_view(request):
    return render(request, 'user_profile/settings.html')

@login_required
def settings_view(request):
    return render(request, 'user_profile/settings.html')

@login_required
def seller_profile_view(request):
    # Временная заглушка для профиля продавца
    return render(request, 'user_profile/settings.html') 