from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates a default superuser'

    def handle(self, *args, **options):
        if not User.objects.filter(phone='+79999999999').exists():
            User.objects.create_superuser(
                phone='+79999999999',
                password='admin',
            )
            self.stdout.write(self.style.SUCCESS('Superuser created successfully'))
        else:
            self.stdout.write(self.style.WARNING('Superuser already exists'))