from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q, Max, Prefetch
from django.utils import timezone
from .models import Dialog, Message, Chat
from catalog.models import Product

@login_required
def dialogs_list(request):
    """Список диалогов пользователя"""
    dialogs = Dialog.objects.filter(participants=request.user)\
        .select_related('product')\
        .prefetch_related('participants')\
        .annotate(last_message_time=Max('messages__created'))\
        .order_by('-last_message_time')
    
    return render(request, 'chat/dialogs_list.html', {'dialogs': dialogs})

@login_required
def dialog_detail(request, dialog_id):
    """Детальная страница диалога с сообщениями"""
    dialog = get_object_or_404(Dialog, id=dialog_id)
    
    # Проверяем права доступа
    if request.user not in dialog.participants.all():
        return HttpResponseForbidden('У вас нет доступа к этому диалогу')
    
    # Отмечаем сообщения как прочитанные
    Message.objects.filter(dialog=dialog)\
        .exclude(sender=request.user)\
        .filter(is_read=False)\
        .update(is_read=True)
    
    messages = dialog.messages.select_related('sender').all()
    
    return render(request, 'chat/dialog_detail.html', {
        'dialog': dialog,
        'messages': messages
    })

@login_required
def send_message(request, dialog_id):
    """API для отправки сообщения"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается'}, status=405)
    
    dialog = get_object_or_404(Dialog, id=dialog_id)
    
    # Проверяем права доступа
    if request.user not in dialog.participants.all():
        return HttpResponseForbidden('У вас нет доступа к этому диалогу')
    
    text = request.POST.get('text', '').strip()
    
    if not text:
        return JsonResponse({'error': 'Текст сообщения не может быть пустым'}, status=400)
    
    message = Message.objects.create(
        dialog=dialog,
        sender=request.user,
        text=text
    )
    
    # Обновляем время последнего сообщения в диалоге
    dialog.updated = timezone.now()
    dialog.save()
    
    return JsonResponse({
        'id': message.id,
        'text': message.text,
        'created': message.created.strftime('%Y-%m-%d %H:%M:%S'),
        'sender_name': message.sender.get_full_name(),
        'is_own': True
    })

@login_required
def get_new_messages(request, dialog_id):
    """API для получения новых сообщений"""
    dialog = get_object_or_404(Dialog, id=dialog_id)
    
    # Проверяем права доступа
    if request.user not in dialog.participants.all():
        return HttpResponseForbidden('У вас нет доступа к этому диалогу')
    
    last_message_id = request.GET.get('last_id')
    
    messages_query = dialog.messages.select_related('sender')
    
    if last_message_id:
        messages_query = messages_query.filter(id__gt=last_message_id)
    
    messages = messages_query.all()
    
    # Отмечаем полученные сообщения как прочитанные
    messages.exclude(sender=request.user).filter(is_read=False).update(is_read=True)
    
    return JsonResponse({
        'messages': [{
            'id': msg.id,
            'text': msg.text,
            'created': msg.created.strftime('%Y-%m-%d %H:%M:%S'),
            'sender_name': msg.sender.get_full_name(),
            'is_own': msg.sender == request.user
        } for msg in messages]
    })

@login_required
def create_dialog(request, product_id):
    """Создание нового диалога"""
    product = get_object_or_404(Product, id=product_id)
    
    # Проверяем, не пытается ли пользователь создать диалог с самим собой
    if product.seller == request.user:
        return JsonResponse(
            {'error': 'Нельзя создать диалог с самим собой'},
            status=400
        )
    
    # Проверяем, существует ли уже диалог
    existing_dialog = Dialog.objects.filter(
        participants=request.user,
        product=product
    ).first()
    
    if existing_dialog:
        return JsonResponse(
            {'error': 'Диалог уже существует'},
            status=400
        )
    
    # Создаем новый диалог
    dialog = Dialog.objects.create(product=product)
    dialog.participants.add(request.user, product.seller)
    
    return redirect('chat:dialog_detail', dialog_id=dialog.id)

@login_required
def chat_list(request):
    """Список чатов пользователя"""
    chats = Chat.objects.filter(participants=request.user)
    return render(request, 'chat/dialogs_list.html', {'chats': chats})

@login_required
def chat_detail(request, chat_id):
    """Детальная страница чата"""
    chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
    return render(request, 'chat/dialog_detail.html', {'chat': chat})

@login_required
def create_chat(request, user_id):
    """Создание нового чата"""
    # Здесь будет логика создания чата
    return redirect('chat:list') 