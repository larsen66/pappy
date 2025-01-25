from django.contrib import admin
from .models import Swipe, SwipeHistory

@admin.register(Swipe)
class SwipeAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'direction', 'created_at']
    list_filter = ['direction', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__phone', 'product__title']
    date_hierarchy = 'created_at'
    readonly_fields = ['user', 'product', 'direction', 'created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(SwipeHistory)
class SwipeHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__phone', 'product__title']
    date_hierarchy = 'viewed_at'
    readonly_fields = ['user', 'product', 'viewed_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False 