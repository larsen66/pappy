from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from .models import Achievement, UserAchievement, Badge, UserBadge
from .services import AchievementService, BadgeService

@login_required
def achievements_list(request):
    """Отображает список достижений пользователя"""
    # Обновляем достижения пользователя
    AchievementService.check_achievements(request.user)
    
    # Получаем достижения пользователя
    user_achievements = UserAchievement.objects.filter(
        user=request.user
    ).select_related('achievement')
    
    # Получаем все доступные достижения
    all_achievements = Achievement.objects.filter(is_active=True)
    
    # Группируем достижения по категориям
    achievements_by_category = {}
    for achievement in all_achievements:
        if achievement.category not in achievements_by_category:
            achievements_by_category[achievement.category] = {
                'name': achievement.get_category_display(),
                'earned': [],
                'available': []
            }
        
        user_achievement = user_achievements.filter(achievement=achievement).first()
        if user_achievement:
            achievements_by_category[achievement.category]['earned'].append({
                'achievement': achievement,
                'user_achievement': user_achievement
            })
        else:
            achievements_by_category[achievement.category]['available'].append(achievement)
    
    context = {
        'achievements_by_category': achievements_by_category,
        'total_earned': user_achievements.count(),
        'total_available': all_achievements.count(),
        'total_points': user_achievements.aggregate(
            total_points=Sum('achievement__points')
        )['total_points'] or 0
    }
    
    return render(request, 'achievements/achievements_list.html', context)

@login_required
def badges_list(request):
    """Отображает список значков пользователя"""
    # Обновляем значки пользователя
    BadgeService.check_badges(request.user)
    
    # Получаем значки пользователя
    user_badges = UserBadge.objects.filter(
        user=request.user
    ).select_related('badge')
    
    # Получаем все доступные значки
    all_badges = Badge.objects.all()
    
    # Разделяем значки на полученные и доступные
    earned_badges = []
    available_badges = []
    
    for badge in all_badges:
        user_badge = user_badges.filter(badge=badge).first()
        if user_badge:
            earned_badges.append({
                'badge': badge,
                'user_badge': user_badge
            })
        else:
            available_badges.append(badge)
    
    context = {
        'earned_badges': earned_badges,
        'available_badges': available_badges,
        'total_earned': len(earned_badges),
        'total_available': len(available_badges)
    }
    
    return render(request, 'achievements/badges_list.html', context)

@login_required
def achievement_detail(request, achievement_id):
    """Отображает детальную информацию о достижении"""
    achievement = Achievement.objects.get(id=achievement_id)
    user_achievement = UserAchievement.objects.filter(
        user=request.user,
        achievement=achievement
    ).first()
    
    if not user_achievement:
        # Получаем прогресс даже для неполученных достижений
        progress = AchievementService._get_progress(request.user, achievement)
    else:
        progress = user_achievement.progress
    
    context = {
        'achievement': achievement,
        'user_achievement': user_achievement,
        'progress': progress
    }
    
    return render(request, 'achievements/achievement_detail.html', context)

@login_required
def badge_detail(request, badge_id):
    """Отображает детальную информацию о значке"""
    badge = Badge.objects.get(id=badge_id)
    user_badge = UserBadge.objects.filter(
        user=request.user,
        badge=badge
    ).first()
    
    context = {
        'badge': badge,
        'user_badge': user_badge,
        'requirements_met': BadgeService._check_requirements(request.user, badge)
    }
    
    return render(request, 'achievements/badge_detail.html', context) 