from django import template
from user_profile.models import SpecialistProfile

register = template.Library()

@register.filter
def is_specialist(value):
    return isinstance(value, SpecialistProfile) 