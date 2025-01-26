from django.contrib import admin
from django.utils.html import format_html
from .models import Chat, Message

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    filter_horizontal = ('participants',)
    date_hierarchy = 'created_at'
    search_fields = ('participants__phone',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('chat', 'sender', 'text', 'created_at', 'is_read')
    list_filter = ('chat', 'created_at', 'is_read')
    readonly_fields = ('chat', 'sender', 'created_at')
    date_hierarchy = 'created_at'
    search_fields = ('text', 'sender__phone')
    
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