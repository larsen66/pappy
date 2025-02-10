import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User

def create_superuser():
    if not User.objects.filter(username='+79999999999').exists():
        User.objects.create_superuser(
            username='+79999999999',
            password='admin',
        )
        print('Superuser created successfully')
    else:
        print('Superuser already exists')

if __name__ == '__main__':
    create_superuser()