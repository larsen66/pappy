from rest_framework_simplejwt.tokens import RefreshToken

def get_token_for_user(user):
    """Генерирует JWT токен для пользователя"""
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token) 