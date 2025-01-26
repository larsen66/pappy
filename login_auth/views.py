from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .models import OneTimeCode
from django.utils.crypto import get_random_string
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from .forms import PhoneLoginForm, ConfirmationCodeForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
import random
from .services import SMSService
import logging
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from user_profile.models import UserProfile

# Настройка логирования
logger = logging.getLogger('zaglushka')
console_logger = logging.getLogger('console')

User = get_user_model()

@require_http_methods(["GET", "POST"])
def phone_login_view(request):
    """Первый шаг - ввод номера телефона"""
    if request.method == "POST":
        form = PhoneLoginForm(request.POST)
        console_logger.info(f"POST data: {request.POST}")
        
        if form.is_valid():
            phone = form.cleaned_data['phone']
            console_logger.info(f"Form is valid. Cleaned data: {form.cleaned_data}")
            
            try:
                console_logger.info(f"Processing phone: {phone}")
                
                # Проверяем существование пользователя
                user = User.objects.filter(phone=phone).first()
                if not user:
                    # Создаем нового пользователя
                    user = User.objects.create_user(phone=phone)
                    console_logger.info(f"Created new user for {phone}")
                
                console_logger.info(f"Phone login attempt: {phone}")
                
                # Генерируем и сохраняем код подтверждения
                verification = OneTimeCode.objects.create(
                    phone=phone,
                    code=SMSService.generate_code(),
                    expires_at=timezone.now() + timezone.timedelta(minutes=10)
                )
                console_logger.info(f"Generated new code for {phone}")
                console_logger.info(f"Generated verification code: {verification.code}")
                
                # Отправляем SMS
                if not SMSService.send_code(phone, verification.code):
                    raise ValidationError("Ошибка отправки SMS")
                
                # Сохраняем телефон в сессии
                request.session['phone'] = phone
                console_logger.info("Phone saved in session")
                
                # Перенаправляем на страницу ввода кода
                console_logger.info("Redirecting to verify_sms")
                return redirect('login_auth:verify_sms')
                
            except ValidationError as e:
                console_logger.error(f"Validation error: {str(e)}")
                form.add_error(None, str(e))
            except Exception as e:
                console_logger.error(f"Unexpected error in phone_login_view: {str(e)}")
                form.add_error(None, "Произошла ошибка. Пожалуйста, попробуйте снова.")
        else:
            form = PhoneLoginForm()
            console_logger.info("Displaying empty form")
    else:
        form = PhoneLoginForm()
        console_logger.info("Displaying empty form")
    
    return render(request, 'login_auth/phone_login.html', {'form': form})

@require_http_methods(["GET", "POST"])
def verify_sms_view(request):
    """Страница ввода кода подтверждения"""
    try:
        phone = request.session.get('phone')
        if not phone:
            console_logger.warning("Phone number not found in session")
            return redirect('login_auth:phone_login')
        
        if request.method == 'POST':
            code = request.POST.get('code')
            if code:
                verification = OneTimeCode.objects.filter(
                    phone=phone,
                    is_verified=False,
                    expires_at__gt=timezone.now()
                ).first()
                
                if not verification:
                    console_logger.warning(f"No valid verification code found for phone {phone}")
                    messages.error(request, 'Код подтверждения истек или не существует')
                    return redirect('login_auth:phone_login')
                
                success, error = verification.verify(code)
                if success:
                    # Создаем или получаем пользователя
                    user = User.objects.filter(phone=phone).first()
                    if not user:
                        console_logger.info(f"Creating new user for phone {phone}")
                        user = User.objects.create_user(phone=phone)
                        UserProfile.objects.create(user=user, is_onboarded=False)
                    
                    auth_login(request, user)
                    console_logger.info(f"User {phone} successfully logged in")
                    
                    # Проверяем статус онбординга
                    if not user.userprofile.is_onboarded:
                        console_logger.info(f"Redirecting user {phone} to onboarding")
                        return redirect('user_profile:onboarding')
                    else:
                        console_logger.info(f"Redirecting user {phone} to profile settings")
                        return redirect('user_profile:settings')
                else:
                    console_logger.warning(f"Invalid code verification for phone {phone}: {error}")
                    messages.error(request, error)
        
        return render(request, 'login_auth/verify.html')
        
    except Exception as e:
        console_logger.error(f'Error in verify_sms_view: {str(e)}', exc_info=True)
        messages.error(request, 'Произошла временная ошибка. Пожалуйста, попробуйте позже.')
        return render(request, 'login_auth/verify.html')

@require_http_methods(['GET', 'POST'])
def signup(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = PhoneLoginForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            
            # Проверяем, не существует ли уже пользователь с таким телефоном
            if User.objects.filter(phone=phone).exists():
                messages.error(request, 'Пользователь с таким номером телефона уже существует')
                return redirect('login_auth:phone_login')
            
            # Создаем новый код подтверждения
            verification = OneTimeCode.objects.create(
                phone=phone,
                code=''.join(random.choices('0123456789', k=OneTimeCode.CODE_LENGTH)),
                expires_at=timezone.now() + timedelta(minutes=OneTimeCode.EXPIRY_TIME_MINUTES)
            )
            
            # Сохраняем телефон в сессии
            request.session['phone'] = phone
            
            # Отправляем код подтверждения
            sms_service = SMSService()
            sms_service.send_sms(phone, f'Ваш код подтверждения: {verification.code}')
            
            messages.success(request, 'Код подтверждения отправлен на ваш телефон')
            return redirect('login_auth:sms_validation')
    else:
        form = PhoneLoginForm()
    
    return render(request, 'login_auth/register.html', {'form': form})

def signup_success(request):
    return render(request, 'login_auth/signup_success.html')

def verify(request):
    """Страница ввода кода подтверждения"""
    try:
        phone = request.session.get('phone')
        if not phone:
            return redirect('login_auth:phone_login')
        
        if request.method == 'POST':
            code = request.POST.get('code')
            if code:
                verification = OneTimeCode.objects.filter(
                    phone=phone,
                    is_verified=False,
                    expires_at__gt=timezone.now()
                ).first()
                
                if not verification:
                    messages.error(request, 'Код подтверждения истек или не существует')
                    return redirect('login_auth:phone_login')
                
                success, error = verification.verify(code)
                if success:
                    # Создаем или получаем пользователя
                    user, created = User.objects.get_or_create(phone=phone)
                    auth_login(request, user)
                    return redirect('user_profile:settings')
                else:
                    messages.error(request, error)
        
        return render(request, 'login_auth/verify.html')
        
    except Exception as e:
        logger.error(f'Ошибка при проверке кода: {str(e)}', exc_info=True)
        messages.error(request, 'Произошла временная ошибка. Пожалуйста, попробуйте позже.')
        return render(request, 'login_auth/verify.html')

@require_http_methods(["POST"])
def resend_code_view(request):
    """Повторная отправка SMS кода"""
    try:
        phone = request.session.get('phone')
        if not phone:
            logger.warning("Resend code attempt without phone in session")
            return JsonResponse({'error': 'Телефон не указан'}, status=400)
        
        # Проверяем существование пользователя
        user = User.objects.filter(phone=phone).first()
        if user and not user.is_active:
            logger.warning(f"Resend code attempt for inactive user: {phone}")
            return JsonResponse({'error': 'Аккаунт заблокирован'}, status=403)
        
        # Проверяем, не слишком ли часто запрашивают код
        last_code = OneTimeCode.objects.filter(phone=phone).order_by('-created_at').first()
        if last_code and (timezone.now() - last_code.created_at).total_seconds() < 60:
            logger.warning(f"Too frequent resend code attempts for {phone}")
            return JsonResponse({
                'error': 'Пожалуйста, подождите минуту перед повторной отправкой'
            }, status=429)
        
        # Создаем новый код
        verification = OneTimeCode.generate_code(phone)
        
        # Отправляем код
        if SMSService.send_code(phone, verification.code):
            logger.info(f"Successfully resent code to {phone}")
            return JsonResponse({'message': 'Код отправлен'})
        else:
            logger.error(f"Failed to send SMS to {phone}")
            return JsonResponse({'error': 'Ошибка отправки SMS'}, status=500)
    
    except Exception as e:
        logger.error(f"Unexpected error in resend_code_view: {str(e)}", exc_info=True)
        return JsonResponse(
            {'error': 'Временная ошибка, пожалуйста, повторите запрос'},
            status=500
        )

@require_http_methods(["GET", "POST"])
def gosuslugi_view(request):
    """Заглушка для авторизации через Госуслуги"""
    try:
        if request.method == 'POST':
            # В реальном приложении здесь была бы интеграция с API Госуслуг
            # Для демонстрации создаем тестового пользователя
            test_phone = '+79991234567'
            user, created = User.objects.get_or_create(
                phone=test_phone,
                defaults={
                    'is_verified': True,
                }
            )
            auth_login(request, user)
            return redirect('user_profile:settings')
            
        return render(request, 'login_auth/gosuslugi.html')
        
    except Exception as e:
        logger.error(f'Ошибка при авторизации через Госуслуги: {str(e)}', exc_info=True)
        messages.error(request, 'Произошла временная ошибка. Пожалуйста, попробуйте позже.')
        return render(request, 'login_auth/gosuslugi.html')

@login_required
def logout_view(request):
    """Выход из системы"""
    auth_logout(request)
    return redirect('login_auth:phone_login')

@require_http_methods(['GET', 'POST'])
def confirm_code(request):
    """Подтверждение кода для регистрации или входа"""
    phone = request.session.get('phone')
    if not phone:
        messages.error(request, 'Сначала введите номер телефона')
        return redirect('login_auth:login')
    
    if request.method == 'POST':
        form = ConfirmationCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            
            try:
                verification = OneTimeCode.objects.get(
                    phone=phone,
                    is_verified=False,
                    expires_at__gt=timezone.now()
                )
                
                if verification.attempts >= OneTimeCode.MAX_VERIFICATION_ATTEMPTS:
                    messages.error(request, 'Превышено максимальное количество попыток. Запросите новый код.')
                    return redirect('login_auth:login')
                
                if verification.code != code:
                    verification.attempts += 1
                    verification.save()
                    messages.error(request, 'Неверный код подтверждения')
                    return render(request, 'login_auth/sms_validation.html', {'form': form})
                
                # Код верный, отмечаем как подтвержденный
                verification.is_verified = True
                verification.save()
                
                # Проверяем, существует ли пользователь
                user = User.objects.filter(phone=phone).first()
                if not user:
                    # Создаем нового пользователя
                    user = User.objects.create_user(phone=phone)
                    auth_login(request, user)
                    return redirect('login_auth:signup_success')
                else:
                    # Авторизуем существующего пользователя
                    auth_login(request, user)
                    return redirect('user_profile:settings')
                
            except OneTimeCode.DoesNotExist:
                messages.error(request, 'Код подтверждения истек или не существует')
                return redirect('login_auth:login')
    else:
        form = ConfirmationCodeForm()
    
    return render(request, 'login_auth/sms_validation.html', {'form': form})

def onboarding(request):
    """Онбординг для новых пользователей"""
    return render(request, 'login_auth/onboarding.html', {
        'title': _('Добро пожаловать в Паппи')
    })

@login_required
def become_seller(request):
    """Страница для подачи заявки на статус продавца"""
    if request.user.is_seller:
        messages.info(request, _('Вы уже являетесь продавцом'))
        return redirect('user_profile:settings')
    
    if request.method == 'POST':
        # TODO: Добавить форму для загрузки документов
        messages.success(request, _('Ваша заявка принята. Мы свяжемся с вами в ближайшее время.'))
        return redirect('user_profile:settings')
    
    return render(request, 'login_auth/become_seller.html', {
        'title': _('Стать продавцом')
    })

@login_required
def become_specialist(request):
    """Страница для подачи заявки на статус специалиста"""
    if request.user.is_specialist:
        messages.info(request, _('Вы уже являетесь специалистом'))
        return redirect('user_profile:settings')
    
    if request.method == 'POST':
        # TODO: Добавить форму для загрузки документов
        messages.success(request, _('Ваша заявка принята. Мы свяжемся с вами в ближайшее время.'))
        return redirect('user_profile:settings')
    
    return render(request, 'login_auth/become_specialist.html', {
        'title': _('Стать специалистом')
    }) 