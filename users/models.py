from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    # Location fields
    last_latitude = models.DecimalField(
        _('Last Known Latitude'),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    last_longitude = models.DecimalField(
        _('Last Known Longitude'),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    
    # Profile fields
    phone = models.CharField(_('Phone Number'), max_length=20, blank=True)
    is_shelter = models.BooleanField(_('Is Shelter'), default=False)
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        indexes = [
            models.Index(fields=['last_latitude', 'last_longitude']),
        ] 