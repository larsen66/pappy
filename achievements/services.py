from django.db.models import Count, Q
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from .models import Achievement, UserAchievement, Badge, UserBadge

class AchievementService:
    """Сервис для работы с достижениями"""
    
    @staticmethod
    def check_achievements(user):
        """Проверяет и присваивает достижения пользователю"""
        achievements = Achievement.objects.filter(is_active=True)
        
        for achievement in achievements:
            if not UserAchievement.objects.filter(user=user, achievement=achievement).exists():
                if AchievementService._check_condition(user, achievement):
                    UserAchievement.objects.create(
                        user=user,
                        achievement=achievement,
                        progress=AchievementService._get_progress(user, achievement)
                    )
    
    @staticmethod
    def _check_condition(user, achievement):
        """Проверяет выполнение условия достижения"""
        condition = achievement.condition
        
        if condition['type'] == 'count':
            return AchievementService._check_count_condition(user, condition)
        elif condition['type'] == 'streak':
            return AchievementService._check_streak_condition(user, condition)
        elif condition['type'] == 'combination':
            return AchievementService._check_combination_condition(user, condition)
        
        return False
    
    @staticmethod
    def _check_count_condition(user, condition):
        """Проверяет условие по количеству"""
        model = ContentType.objects.get(
            app_label=condition['model']['app'],
            model=condition['model']['name']
        ).model_class()
        
        count = model.objects.filter(
            **{condition['field']: user}
        ).count()
        
        return count >= condition['value']
    
    @staticmethod
    def _check_streak_condition(user, condition):
        """Проверяет условие по последовательности"""
        model = ContentType.objects.get(
            app_label=condition['model']['app'],
            model=condition['model']['name']
        ).model_class()
        
        dates = model.objects.filter(
            **{condition['field']: user}
        ).dates('created_at', 'day')
        
        streak = 0
        prev_date = None
        
        for date in dates:
            if prev_date and (date - prev_date).days == 1:
                streak += 1
            else:
                streak = 1
            prev_date = date
            
            if streak >= condition['value']:
                return True
        
        return False
    
    @staticmethod
    def _check_combination_condition(user, condition):
        """Проверяет комбинированное условие"""
        return all(
            AchievementService._check_condition(user, subcondition)
            for subcondition in condition['conditions']
        )
    
    @staticmethod
    def _get_progress(user, achievement):
        """Получает прогресс достижения"""
        condition = achievement.condition
        
        if condition['type'] == 'count':
            model = ContentType.objects.get(
                app_label=condition['model']['app'],
                model=condition['model']['name']
            ).model_class()
            
            current = model.objects.filter(
                **{condition['field']: user}
            ).count()
            
            return {
                'current': current,
                'target': condition['value'],
                'percentage': min(100, int(current / condition['value'] * 100))
            }
        
        return {}

class BadgeService:
    """Сервис для работы со значками"""
    
    @staticmethod
    def check_badges(user):
        """Проверяет и присваивает значки пользователю"""
        badges = Badge.objects.all()
        
        for badge in badges:
            if not UserBadge.objects.filter(user=user, badge=badge).exists():
                if BadgeService._check_requirements(user, badge):
                    UserBadge.objects.create(
                        user=user,
                        badge=badge
                    )
    
    @staticmethod
    def _check_requirements(user, badge):
        """Проверяет выполнение требований значка"""
        requirements = badge.requirements
        
        if requirements['type'] == 'achievements':
            return BadgeService._check_achievements_requirement(user, requirements)
        elif requirements['type'] == 'activity':
            return BadgeService._check_activity_requirement(user, requirements)
        
        return False
    
    @staticmethod
    def _check_achievements_requirement(user, requirements):
        """Проверяет требования по достижениям"""
        achievements = UserAchievement.objects.filter(user=user)
        
        if 'category' in requirements:
            achievements = achievements.filter(
                achievement__category=requirements['category']
            )
        
        if 'level' in requirements:
            achievements = achievements.filter(
                achievement__level=requirements['level']
            )
        
        return achievements.count() >= requirements.get('count', 1)
    
    @staticmethod
    def _check_activity_requirement(user, requirements):
        """Проверяет требования по активности"""
        activity_type = requirements['activity_type']
        
        if activity_type == 'announcements':
            count = user.announcements.count()
        elif activity_type == 'reviews':
            count = user.reviews.count()
        elif activity_type == 'helps':
            count = user.helped_pets.count()
        else:
            return False
        
        return count >= requirements.get('count', 1) 