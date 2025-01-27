from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models import UserPreferences, UserInteraction
from .services import MatchingService, RecommendationService
from .forms import UserPreferencesForm

@login_required
def preferences_update(request):
    """Обновление предпочтений пользователя"""
    preferences = UserPreferences.objects.get_or_create(user=request.user)[0]
    
    if request.method == 'POST':
        form = UserPreferencesForm(request.POST, instance=preferences)
        if form.is_valid():
            form.save()
            messages.success(request, _('Ваши предпочтения обновлены'))
            return redirect('matcher:matches')
    else:
        form = UserPreferencesForm(instance=preferences)
    
    return render(request, 'matcher/preferences_form.html', {
        'form': form
    })

@login_required
def matches_list(request):
    """Список подходящих животных"""
    matching_service = MatchingService(request.user)
    matches = matching_service.get_matches(limit=50)
    
    # Пагинация
    paginator = Paginator(matches, 12)
    page = request.GET.get('page')
    matches = paginator.get_page(page)
    
    return render(request, 'matcher/matches_list.html', {
        'matches': matches
    })

@login_required
def recommendations_list(request):
    """Список рекомендованных животных"""
    recommendation_service = RecommendationService(request.user)
    recommendations = recommendation_service.get_recommendations(limit=24)
    
    # Пагинация
    paginator = Paginator(recommendations, 12)
    page = request.GET.get('page')
    recommendations = paginator.get_page(page)
    
    return render(request, 'matcher/recommendations_list.html', {
        'recommendations': recommendations
    })

@login_required
@require_POST
def record_interaction(request):
    """Запись взаимодействия пользователя с животным"""
    animal_id = request.POST.get('animal_id')
    interaction_type = request.POST.get('type')
    
    if not animal_id or not interaction_type:
        return JsonResponse({'error': 'Missing required parameters'}, status=400)
    
    if interaction_type not in dict(UserInteraction.INTERACTION_TYPES):
        return JsonResponse({'error': 'Invalid interaction type'}, status=400)
    
    try:
        interaction = UserInteraction.objects.create(
            user=request.user,
            animal_id=animal_id,
            interaction_type=interaction_type
        )
        return JsonResponse({
            'status': 'success',
            'interaction_id': interaction.id
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def interaction_history(request):
    """История взаимодействий пользователя"""
    interactions = UserInteraction.objects.filter(
        user=request.user
    ).select_related(
        'animal',
        'animal__announcement'
    ).order_by('-created_at')
    
    # Пагинация
    paginator = Paginator(interactions, 20)
    page = request.GET.get('page')
    interactions = paginator.get_page(page)
    
    return render(request, 'matcher/interaction_history.html', {
        'interactions': interactions
    }) 