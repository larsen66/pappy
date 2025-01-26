# Generated by Django 5.1.5 on 2025-01-25 23:39

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('login_auth', '0002_onetimecode'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='onetimecode',
            options={'verbose_name': 'Код подтверждения', 'verbose_name_plural': 'Коды подтверждения'},
        ),
        migrations.AlterField(
            model_name='onetimecode',
            name='attempts',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='onetimecode',
            name='code',
            field=models.CharField(max_length=4),
        ),
        migrations.AlterField(
            model_name='onetimecode',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='onetimecode',
            name='expires_at',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='onetimecode',
            name='is_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='onetimecode',
            name='phone',
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name='user',
            name='phone',
            field=models.CharField(max_length=20, unique=True, verbose_name='Телефон'),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('avatar', models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Аватар')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='Имя')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='Фамилия')),
                ('bio', models.TextField(blank=True, verbose_name='О себе')),
                ('is_onboarded', models.BooleanField(default=False, verbose_name='Прошел онбординг')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Профиль пользователя',
                'verbose_name_plural': 'Профили пользователей',
            },
        ),
    ]
