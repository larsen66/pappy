from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
import os

class Command(BaseCommand):
    help = 'Creates a superuser from environment variables'

    def handle(self, *args, **options):
        if not User.objects.filter(username=os.environ.get('DJANGO_SUPERUSER_USERNAME')).exists():
            User.objects.create_superuser(
                username=os.environ.get('DJANGO_SUPERUSER_USERNAME'),
                password=os.environ.get('DJANGO_SUPERUSER_PASSWORD'),
                email=os.environ.get('DJANGO_SUPERUSER_EMAIL')
            )
            self.stdout.write(self.style.SUCCESS('Superuser created successfully'))
        else:
            self.stdout.write(self.style.WARNING('Superuser already exists'))