from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import Notification, NotificationPreference, PushToken
from .services import NotificationService
from .forms import NotificationPreferenceForm

@login_required
def notification_list(request):
    """Список уведомлений пользователя"""
    # Получаем все уведомления пользователя
    notifications = Notification.objects.filter(
        user=request.user
    ).select_related(
        'content_type'
    ).order_by('-created_at')
    
    # Фильтрация
    notification_type = request.GET.get('type')
    if notification_type:
        notifications = notifications.filter(notification_type=notification_type)
    
    # Фильтр по прочитанным/непрочитанным
    is_read = request.GET.get('is_read')
    if is_read is not None:
        notifications = notifications.filter(is_read=is_read == 'true')
    
    # Пагинация
    paginator = Paginator(notifications, 20)
    page = request.GET.get('page')
    notifications = paginator.get_page(page)
    
    # Получаем количество непрочитанных
    unread_count = NotificationService.get_unread_count(request.user)
    
    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications,
        'unread_count': unread_count,
        'current_type': notification_type,
        'current_is_read': is_read,
    })

@login_required
def notification_preferences(request):
    """Настройки уведомлений"""
    preferences = NotificationPreference.objects.get_or_create(user=request.user)[0]
    
    if request.method == 'POST':
        form = NotificationPreferenceForm(request.POST, instance=preferences)
        if form.is_valid():
            form.save()
            messages.success(request, _('Настройки уведомлений обновлены'))
            return redirect('notifications:preferences')
    else:
        form = NotificationPreferenceForm(instance=preferences)
    
    return render(request, 'notifications/preferences.html', {
        'form': form,
        'preferences': preferences,
    })

@login_required
@require_POST
def mark_as_read(request):
    """Отметить уведомления как прочитанные"""
    notification_ids = request.POST.getlist('notification_ids[]')
    
    if notification_ids:
        NotificationService.mark_as_read(request.user, notification_ids)
    else:
        # Если ID не указаны, отмечаем все как прочитанные
        NotificationService.mark_as_read(request.user)
    
    return JsonResponse({'status': 'success'})

@login_required
@require_POST
def register_push_token(request):
    """Регистрация push-токена"""
    token = request.POST.get('token')
    device_type = request.POST.get('device_type')
    
    if not token or not device_type:
        return JsonResponse({
            'status': 'error',
            'message': _('Не указан токен или тип устройства')
        }, status=400)
    
    try:
        token_obj = NotificationService.register_push_token(
            request.user,
            token,
            device_type
        )
        return JsonResponse({
            'status': 'success',
            'token_id': token_obj.id
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required
@require_POST
def unregister_push_token(request):
    """Отключение push-токена"""
    token = request.POST.get('token')
    
    if not token:
        return JsonResponse({
            'status': 'error',
            'message': _('Не указан токен')
        }, status=400)
    
    try:
        NotificationService.unregister_push_token(request.user, token)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required
def notification_detail(request, pk):
    """Детальная информация об уведомлении"""
    notification = get_object_or_404(
        Notification.objects.select_related('content_type'),
        pk=pk,
        user=request.user
    )
    
    if not notification.is_read:
        NotificationService.mark_as_read(request.user, [notification.id])
    
    return render(request, 'notifications/notification_detail.html', {
        'notification': notification
    })

@login_required
def mark_notification_read(request, notification_id):
    """Отметить уведомление как прочитанное"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})

@login_required
def mark_all_read(request):
    """Отметить все уведомления как прочитанные"""
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})

@login_required
def get_unread_count(request):
    """Получить количество непрочитанных уведомлений"""
    count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({'count': count})

@login_required
def delete_notification(request, notification_id):
    """Удалить уведомление"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.delete()
    return JsonResponse({'status': 'success'}) 