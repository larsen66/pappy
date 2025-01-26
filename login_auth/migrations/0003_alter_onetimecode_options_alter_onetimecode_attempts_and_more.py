# Generated by Django 5.1.5 on 2025-01-25 22:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('login_auth', '0002_alter_onetimecode_options_alter_onetimecode_attempts_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='onetimecode',
            options={'ordering': ['-created_at'], 'verbose_name': 'Код подтверждения', 'verbose_name_plural': 'Коды подтверждения'},
        ),
        migrations.AlterField(
            model_name='onetimecode',
            name='attempts',
            field=models.IntegerField(default=0, verbose_name='Попытки'),
        ),
        migrations.AlterField(
            model_name='onetimecode',
            name='code',
            field=models.CharField(max_length=4, verbose_name='Код подтверждения'),
        ),
        migrations.AlterField(
            model_name='onetimecode',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Создан'),
        ),
        migrations.AlterField(
            model_name='onetimecode',
            name='expires_at',
            field=models.DateTimeField(verbose_name='Истекает'),
        ),
        migrations.AlterField(
            model_name='onetimecode',
            name='is_verified',
            field=models.BooleanField(default=False, verbose_name='Подтвержден'),
        ),
        migrations.AlterField(
            model_name='onetimecode',
            name='phone',
            field=models.CharField(max_length=20, verbose_name='Номер телефона'),
        ),
    ]
