# Generated by Django 5.1.5 on 2025-01-25 22:47

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('login_auth', '0003_alter_onetimecode_options_alter_onetimecode_attempts_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='дата регистрации'),
        ),
        migrations.AlterField(
            model_name='onetimecode',
            name='phone',
            field=models.CharField(max_length=17, verbose_name='Номер телефона'),
        ),
    ]
