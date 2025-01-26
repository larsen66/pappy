from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
import logging
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from .forms import PhoneLoginForm, SMSVerificationForm
from .models import User, OneTimeCode
from .services import SMSService, GosuslugiService
import random
from user_profile.models import UserProfile

logger = logging.getLogger('zaglushka')

# Создаем логгер для вывода в терминал
console_logger = logging.getLogger('console')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('[%(levelname)s] %(message)s')
console_handler.setFormatter(console_formatter)
console_logger.addHandler(console_handler)
console_logger.setLevel(logging.DEBUG)

# Create your views here.

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('/')
    else:
        form = AuthenticationForm()
    return render(request, 'login_auth/login.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/')
    else:
        form = UserCreationForm()
    return render(request, 'login_auth/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('/')

@require_http_methods(["GET", "POST"])
def phone_login_view(request):
    """Первый шаг - ввод телефона"""
    try:
        if request.method == "POST":
            form = PhoneLoginForm(request.POST)
            if form.is_valid():
                phone = form.cleaned_data['phone']
                
                with transaction.atomic():
                    # Проверяем существование пользователя
                    user = User.objects.filter(phone=phone).first()
                    
                    if user:
                        # Проверяем статус существующего пользователя
                        if not user.is_active:
                            logger.warning(f"Attempt to login with inactive account: {phone}")
                            raise ValidationError("Аккаунт заблокирован. Обратитесь в поддержку.")
                        
                        logger.info(f"Existing user login attempt: {phone}")
                    else:
                        # Создаем нового пользователя
                        username = f"user_{phone}"  # Генерируем временный username
                        user = User.objects.create(
                            phone=phone,
                            username=username,
                            is_active=True
                        )
                        # Создаем профиль пользователя
                        UserProfile.objects.create(
                            user=user,
                            is_onboarded=False
                        )
                        logger.info(f"Created new user and profile: {phone}")
                    
                    # Очищаем старые коды
                    OneTimeCode.objects.filter(phone=phone).delete()
                    
                    # Создаем новый код подтверждения
                    code = ''.join(random.choices('0123456789', k=4))
                    verification = OneTimeCode.objects.create(
                        phone=phone,
                        code=code,
                        expires_at=timezone.now() + timezone.timedelta(minutes=5)
                    )
                    
                    # Отправляем SMS
                    if not SMSService.send_code(phone, code):
                        logger.error(f"Failed to send SMS to {phone}")
                        raise ValidationError("Ошибка отправки SMS")
                    
                    # Сохраняем телефон в сессии
                    request.session['phone'] = phone
                    
                    # Переходим к вводу кода
                    verification_form = SMSVerificationForm(initial={'phone': phone})
                    return render(request, 'login_auth/verify_sms.html', {
                        'form': verification_form,
                        'phone': phone
                    })
        else:
            form = PhoneLoginForm()
        
        return render(request, 'login_auth/phone_login.html', {'form': form})
        
    except ValidationError as e:
        # Ошибки валидации показываем пользователю
        form.add_error(None, str(e))
        return render(request, 'login_auth/phone_login.html', {'form': form})
    except Exception as e:
        # Прочие ошибки логируем и показываем общее сообщение
        logger.error(f"Unexpected error in phone_login_view: {str(e)}", exc_info=True)
        form.add_error(None, "Временная ошибка, пожалуйста, повторите запрос")
        return render(request, 'login_auth/phone_login.html', {'form': form})

@require_http_methods(["GET", "POST"])
def verify_sms_view(request):
    """Второй шаг - проверка SMS кода"""
    try:
        if request.method == "POST":
            form = SMSVerificationForm(request.POST)
            if form.is_valid():
                phone = form.cleaned_data['phone']
                code = form.cleaned_data['code']
                
                console_logger.info(f"Попытка верификации кода для номера {phone}")
                
                # Получаем пользователя
                try:
                    user = User.objects.get(phone=phone)
                    console_logger.info(f"Найден пользователь: {user.phone}")
                except User.DoesNotExist:
                    console_logger.error(f"Пользователь не найден: {phone}")
                    raise ValidationError("Пользователь не найден")
                
                # Проверяем код
                verification = OneTimeCode.objects.filter(
                    phone=phone,
                    is_verified=False,
                    expires_at__gt=timezone.now()
                ).first()
                
                if not verification:
                    console_logger.warning(f"Не найден действующий код для {phone}")
                    raise ValidationError("Код подтверждения истек или не существует")
                
                if verification.is_blocked():
                    console_logger.warning(f"Превышено количество попыток для {phone}")
                    raise ValidationError("Превышено количество попыток. Запросите новый код.")
                
                if verification.code != code:
                    verification.attempts += 1
                    verification.save()
                    console_logger.warning(f"Неверный код для {phone}. Попытка {verification.attempts}")
                    raise ValidationError("Неверный код")
                
                # Код верный
                console_logger.info(f"Код подтвержден для {phone}")
                verification.is_verified = True
                verification.save()
                
                # Обновляем время последнего входа
                user.last_login = timezone.now()
                user.save()
                
                # Логиним пользователя
                login(request, user)
                console_logger.info(f"Пользователь {phone} успешно авторизован")
                
                # Очищаем сессию
                if 'phone' in request.session:
                    del request.session['phone']
                
                # Определяем, куда перенаправить пользователя
                try:
                    profile = user.userprofile
                    if not profile.is_onboarded:
                        console_logger.info(f"Редирект на онбординг для {phone}")
                        return redirect('user_profile:onboarding')
                    elif hasattr(user, 'seller_profile'):
                        console_logger.info(f"Редирект на панель продавца для {phone}")
                        return redirect('user_profile:seller_profile')
                    elif hasattr(user, 'specialist_profile'):
                        console_logger.info(f"Редирект на профиль специалиста для {phone}")
                        return redirect('user_profile:specialist_profile')
                    else:
                        console_logger.info(f"Редирект на настройки для {phone}")
                        return redirect('user_profile:settings')
                except Exception as e:
                    console_logger.error(f"Ошибка при определении редиректа для {phone}: {str(e)}")
                    return redirect('user_profile:onboarding')
                
        else:
            # Получаем телефон из GET параметров при первом входе на страницу
            initial_phone = request.GET.get('phone')
            if not initial_phone:
                logger.warning("Attempt to access verify_sms without phone number")
                return redirect('login_auth:phone_login')
            form = SMSVerificationForm(initial={'phone': initial_phone})
        
        return render(request, 'login_auth/verify_sms.html', {
            'form': form,
            'phone': request.GET.get('phone') or form.data.get('phone')
        })
        
    except ValidationError as e:
        # Ошибки валидации показываем пользователю
        form.add_error(None, str(e))
        return render(request, 'login_auth/verify_sms.html', {
            'form': form,
            'phone': form.data.get('phone')
        })
    except Exception as e:
        # Прочие ошибки логируем и показываем общее сообщение
        logger.error(f"Unexpected error in verify_sms_view: {str(e)}", exc_info=True)
        form.add_error(None, "Временная ошибка, пожалуйста, повторите запрос")
        return render(request, 'login_auth/verify_sms.html', {
            'form': form,
            'phone': form.data.get('phone')
        })

@require_http_methods(["POST"])
def resend_code_view(request):
    """Повторная отправка SMS кода"""
    try:
        phone = request.POST.get('phone')
        if not phone:
            logger.warning("Resend code attempt without phone number")
            return JsonResponse({'error': 'Телефон не указан'}, status=400)
        
        # Проверяем существование пользователя
        try:
            user = User.objects.get(phone=phone)
            if not user.is_active:
                logger.warning(f"Resend code attempt for inactive user: {phone}")
                return JsonResponse({'error': 'Аккаунт заблокирован'}, status=403)
        except User.DoesNotExist:
            logger.error(f"Resend code attempt for non-existent user: {phone}")
            return JsonResponse({'error': 'Пользователь не найден'}, status=404)
        
        # Проверяем, не слишком ли часто запрашивают код
        last_code = OneTimeCode.objects.filter(phone=phone).order_by('-created_at').first()
        if last_code and (timezone.now() - last_code.created_at).total_seconds() < 60:
            logger.warning(f"Too frequent resend code attempts for {phone}")
            return JsonResponse({
                'error': 'Пожалуйста, подождите минуту перед повторной отправкой'
            }, status=429)
        
        # Очищаем старые коды
        OneTimeCode.objects.filter(phone=phone).delete()
        
        # Создаем новый код
        code = ''.join(random.choices('0123456789', k=4))
        verification = OneTimeCode.objects.create(
            phone=phone,
            code=code,
            expires_at=timezone.now() + timezone.timedelta(minutes=5)
        )
        
        # Отправляем код
        if SMSService.send_code(phone, code):
            logger.info(f"Successfully resent code to {phone}")
            return JsonResponse({'message': 'Код отправлен'})
        else:
            logger.error(f"Failed to send SMS to {phone}")
            raise ValidationError("Ошибка отправки SMS")
    
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in resend_code_view: {str(e)}", exc_info=True)
        return JsonResponse(
            {'error': 'Временная ошибка, пожалуйста, повторите запрос'},
            status=500
        )

@require_http_methods(["GET", "POST"])
def gosuslugi_view(request):
    """Авторизация через Госуслуги (заглушка)"""
    try:
        if request.method == "POST":
            # В реальности здесь был бы код обработки OAuth
            user_data = GosuslugiService.authenticate("test_token")
            
            user, created = User.objects.get_or_create(
                phone=user_data['phone'],
                defaults={
                    'username': user_data['phone'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name']
                }
            )
            
            login(request, user)
            return redirect('/')
        
        return render(request, 'login_auth/gosuslugi.html')
    
    except Exception as e:
        logger.error(f"Unexpected error in gosuslugi_view: {str(e)}", exc_info=True)
        return render(request, 'login_auth/gosuslugi.html', {
            'error': 'Временная ошибка, пожалуйста, повторите запрос'
        })
