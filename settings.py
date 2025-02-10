import dj_database_url
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

# Update allowed hosts
ALLOWED_HOSTS = ['*.onrender.com', 'localhost', '127.0.0.1']

# Database configuration
if 'DATABASE_URL' in os.environ:
    DATABASES['default'] = dj_database_url.config(
        conn_max_age=600,
        conn_health_checks=True,
    )

# Static files configuration
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MIDDLEWARE = [
    // ... existing middleware ...
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add this line after SecurityMiddleware
    // ... existing middleware ...
] 