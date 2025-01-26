from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse

@login_required
def profile_view(request):
    return render(request, 'user_profile/settings.html')

@login_required
def onboarding_view(request):
    return render(request, 'user_profile/onboarding.html')

@login_required
def settings_view(request):
    return render(request, 'user_profile/settings.html')

@login_required
def seller_profile_view(request):
    # Временная заглушка для профиля продавца
    return render(request, 'user_profile/settings.html')
