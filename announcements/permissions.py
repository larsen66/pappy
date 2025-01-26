from rest_framework import permissions

class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешение, позволяющее только авторам объекта редактировать его.
    """
    def has_object_permission(self, request, view, obj):
        # Разрешаем GET, HEAD или OPTIONS запросы
        if request.method in permissions.SAFE_METHODS:
            return True

        # Разрешаем запись только автору объекта
        return obj.author == request.user

class IsAnnouncementAuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешение, позволяющее только авторам объявления редактировать его изображения.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.announcement.author == request.user

class IsSpecialistOrReadOnly(permissions.BasePermission):
    """
    Разрешение, позволяющее только специалистам создавать объявления об услугах.
    """
    def has_permission(self, request, view):
        # Разрешаем GET, HEAD или OPTIONS запросы
        if request.method in permissions.SAFE_METHODS:
            return True

        # Разрешаем создание только специалистам
        return request.user.is_authenticated and request.user.is_specialist

class IsModeratorOrReadOnly(permissions.BasePermission):
    """
    Разрешение, позволяющее только модераторам изменять статус объявлений.
    """
    def has_permission(self, request, view):
        # Разрешаем GET, HEAD или OPTIONS запросы
        if request.method in permissions.SAFE_METHODS:
            return True

        # Разрешаем модерацию только модераторам
        return request.user.is_authenticated and request.user.is_staff 