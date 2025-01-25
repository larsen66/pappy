# Generated by Django 2.2 on 2019-04-20 12:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('otp_totp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='totpdevice',
            name='throttling_failure_count',
            field=models.PositiveIntegerField(default=0, help_text='Number of successive failed attempts.'),
        ),
        migrations.AddField(
            model_name='totpdevice',
            name='throttling_failure_timestamp',
            field=models.DateTimeField(blank=True, default=None, help_text='A timestamp of the last failed verification attempt. Null if last attempt succeeded.', null=True),
        ),
    ]
