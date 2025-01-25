from django.contrib import admin
from django.utils.html import format_html
from .models import Dialog, Message

@admin.register(Dialog)
class DialogAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'participants_list', 'created', 'updated']
    list_filter = ['created', 'updated']
    search_fields = ['participants__first_name', 'participants__last_name', 'participants__phone', 'product__title']
    date_hierarchy = 'created'
    readonly_fields = ['created', 'updated']
    
    def participants_list(self, obj):
        return ', '.join([user.get_full_name() or user.phone for user in obj.participants.all()])
    participants_list.short_description = 'Участники'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['dialog', 'sender', 'short_text', 'created', 'is_read']
    list_filter = ['is_read', 'created']
    search_fields = ['sender__first_name', 'sender__last_name', 'sender__phone', 'text']
    date_hierarchy = 'created'
    readonly_fields = ['dialog', 'sender', 'created', 'is_read']
    actions = ['mark_as_read', 'mark_as_unread']
    
    def short_text(self, obj):
        max_length = 50
        text = obj.text[:max_length]
        if len(obj.text) > max_length:
            text += '...'
        return text
    short_text.short_description = 'Сообщение'
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f'Отмечено прочитанными: {queryset.count()}')
    mark_as_read.short_description = 'Отметить как прочитанные'
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, f'Отмечено непрочитанными: {queryset.count()}')
    mark_as_unread.short_description = 'Отметить как непрочитанные'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False 