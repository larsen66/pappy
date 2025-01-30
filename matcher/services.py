from django.db.models import Q, F, Value, FloatField
from django.db.models.functions import Cast
from django.contrib.gis.measure import D
from django.utils import timezone
from datetime import timedelta
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from .models import UserPreferences, MatchingScore, UserInteraction, RecommendationHistory, Match
from announcements.models import AnimalAnnouncement, Announcement
from math import radians, sin, cos, sqrt, atan2

class MatchingService:
    """Сервис для умного подбора животных"""
    
    def __init__(self, user):
        self.user = user
        self.preferences = UserPreferences.objects.get_or_create(user=user)[0]
    
    def calculate_base_score(self, animal):
        """Расчет базового скора на основе предпочтений"""
        score = 0
        matched_criteria = []
        
        # Проверяем основные характеристики
        if self.preferences.preferred_species and animal.species in self.preferences.preferred_species:
            score += 20
            matched_criteria.append('species_match')
        
        if self.preferences.preferred_breeds and animal.breed in self.preferences.preferred_breeds:
            score += 15
            matched_criteria.append('breed_match')
        
        if self.preferences.preferred_gender and animal.gender == self.preferences.preferred_gender:
            score += 10
            matched_criteria.append('gender_match')
        
        # Проверяем возраст
        if animal.age:
            if (not self.preferences.preferred_age_min or animal.age >= self.preferences.preferred_age_min) and \
               (not self.preferences.preferred_age_max or animal.age <= self.preferences.preferred_age_max):
                score += 10
                matched_criteria.append('age_match')
        
        # Проверяем размер
        if self.preferences.size_preference and animal.size in self.preferences.size_preference:
            score += 5
            matched_criteria.append('size_match')
        
        # Проверяем окрас
        if self.preferences.color_preference and animal.color in self.preferences.color_preference:
            score += 5
            matched_criteria.append('color_match')
        
        # Проверяем специальные требования
        if self.preferences.requires_pedigree and animal.pedigree:
            score += 5
            matched_criteria.append('pedigree_match')
        if self.preferences.requires_vaccinated and animal.vaccinated:
            score += 5
            matched_criteria.append('vaccinated_match')
        if self.preferences.requires_passport and animal.passport:
            score += 5
            matched_criteria.append('passport_match')
        
        return score, matched_criteria
    
    def apply_location_boost(self, score, animal):
        """Применяем бустинг на основе расстояния"""
        if animal.announcement.latitude and animal.announcement.longitude:
            distance = self.user.profile.location.distance(
                animal.announcement.location
            ).km if self.user.profile.location else float('inf')
            
            if distance <= self.preferences.max_distance:
                distance_factor = 1 - (distance / self.preferences.max_distance)
                return score * (1 + distance_factor * 0.2)
        return score
    
    def apply_interaction_boost(self, score, animal):
        """Применяем бустинг на основе взаимодействий"""
        user_interactions = UserInteraction.objects.filter(
            user=self.user,
            animal__species=animal.species
        )
        
        like_ratio = user_interactions.filter(interaction_type='like').count() / \
                    max(user_interactions.count(), 1)
        
        return score * (1 + like_ratio * 0.1)
    
    def get_matches(self, limit=20):
        """Получение списка подходящих животных"""
        # Получаем базовый queryset
        animals = AnimalAnnouncement.objects.filter(
            announcement__status='active'
        ).exclude(
            matching_scores__user=self.user
        )
        
        # Применяем фильтры предпочтений
        if self.preferences.preferred_species:
            animals = animals.filter(species__in=self.preferences.preferred_species)
        
        if self.preferences.preferred_breeds:
            animals = animals.filter(breed__in=self.preferences.preferred_breeds)
        
        matches = []
        for animal in animals[:100]:  # Ограничиваем для производительности
            base_score, criteria = self.calculate_base_score(animal)
            if base_score > 0:
                final_score = self.apply_location_boost(base_score, animal)
                final_score = self.apply_interaction_boost(final_score, animal)
                
                matches.append({
                    'animal': animal,
                    'score': final_score,
                    'criteria': criteria
                })
        
        # Сортируем и ограничиваем результаты
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches[:limit]
    
    def save_matches(self, matches):
        """Сохранение результатов матчинга"""
        bulk_scores = []
        for match in matches:
            bulk_scores.append(
                MatchingScore(
                    user=self.user,
                    animal=match['animal'],
                    score=match['score'],
                    matched_criteria=match['criteria']
                )
            )
        MatchingScore.objects.bulk_create(bulk_scores)

class RecommendationService:
    """Сервис рекомендаций животных"""
    
    def __init__(self, user):
        self.user = user
        self.matching_service = MatchingService(user)
    
    def get_collaborative_recommendations(self, limit=5):
        """Получение рекомендаций на основе поведения похожих пользователей"""
        # Находим пользователей с похожими взаимодействиями
        user_interactions = UserInteraction.objects.filter(user=self.user)
        similar_users = UserInteraction.objects.filter(
            animal__in=user_interactions.values('animal')
        ).exclude(
            user=self.user
        ).values('user').distinct()
        
        # Получаем животных, с которыми взаимодействовали похожие пользователи
        recommended_animals = AnimalAnnouncement.objects.filter(
            user_interactions__user__in=similar_users,
            user_interactions__interaction_type='like'
        ).exclude(
            user_interactions__user=self.user
        ).distinct()
        
        return recommended_animals[:limit]
    
    def get_content_based_recommendations(self, limit=5):
        """Получение рекомендаций на основе характеристик животных"""
        # Используем последние положительные взаимодействия пользователя
        liked_animals = AnimalAnnouncement.objects.filter(
            user_interactions__user=self.user,
            user_interactions__interaction_type='like'
        ).order_by('-user_interactions__created_at')[:5]
        
        if not liked_animals:
            return []
        
        # Находим похожих животных
        similar_animals = AnimalAnnouncement.objects.filter(
            species__in=liked_animals.values('species'),
            breed__in=liked_animals.values('breed')
        ).exclude(
            id__in=liked_animals.values('id')
        ).distinct()
        
        return similar_animals[:limit]
    
    def get_recommendations(self, limit=10):
        """Получение смешанных рекомендаций"""
        # Получаем рекомендации разных типов
        collaborative_recs = self.get_collaborative_recommendations(limit=limit//2)
        content_based_recs = self.get_content_based_recommendations(limit=limit//2)
        matching_recs = self.matching_service.get_matches(limit=limit//2)
        
        # Объединяем и сохраняем рекомендации
        recommendations = []
        seen_animals = set()
        
        for animal in collaborative_recs:
            if animal.id not in seen_animals:
                recommendations.append({
                    'animal': animal,
                    'score': 0.8,
                    'reason': {'type': 'collaborative'}
                })
                seen_animals.add(animal.id)
        
        for animal in content_based_recs:
            if animal.id not in seen_animals:
                recommendations.append({
                    'animal': animal,
                    'score': 0.7,
                    'reason': {'type': 'content_based'}
                })
                seen_animals.add(animal.id)
        
        for match in matching_recs:
            if match['animal'].id not in seen_animals:
                recommendations.append({
                    'animal': match['animal'],
                    'score': match['score'] / 100,
                    'reason': {'type': 'matching', 'criteria': match['criteria']}
                })
                seen_animals.add(match['animal'].id)
        
        # Сортируем по скору
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        recommendations = recommendations[:limit]
        
        # Сохраняем историю рекомендаций
        self.save_recommendations(recommendations)
        
        return recommendations
    
    def save_recommendations(self, recommendations):
        """Сохранение истории рекомендаций"""
        bulk_history = []
        for rec in recommendations:
            bulk_history.append(
                RecommendationHistory(
                    user=self.user,
                    animal=rec['animal'],
                    score=rec['score'],
                    reason=rec['reason']
                )
            )
        RecommendationHistory.objects.bulk_create(bulk_history)

def update_matching_scores():
    """Периодическое обновление скоров матчинга"""
    # Удаляем старые скоры
    MatchingScore.objects.filter(
        created_at__lt=timezone.now() - timedelta(days=7)
    ).delete()
    
    # Обновляем скоры для активных пользователей
    active_users = UserInteraction.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    ).values('user').distinct()
    
    for user_dict in active_users:
        matching_service = MatchingService(user_dict['user'])
        matches = matching_service.get_matches()
        matching_service.save_matches(matches)

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # радиус Земли в километрах

    lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return distance

def find_matches(user, preferences):
    """
    Находит объявления, соответствующие предпочтениям пользователя
    """
    # Базовый запрос
    announcements = Announcement.objects.filter(is_active=True)
    
    # Фильтрация по виду животного
    if preferences.get('species'):
        announcements = announcements.filter(
            animal_details__species__in=preferences['species']
        )
    
    # Фильтрация по породе
    if preferences.get('breeds'):
        announcements = announcements.filter(
            animal_details__breed__in=preferences['breeds']
        )
    
    # Фильтрация по размеру
    if preferences.get('size'):
        announcements = announcements.filter(
            animal_details__size__in=preferences['size']
        )
    
    # Фильтрация по цвету
    if preferences.get('color'):
        announcements = announcements.filter(
            animal_details__color__in=preferences['color']
        )
    
    # Фильтрация по местоположению
    if preferences.get('location'):
        lat = preferences['location'].get('latitude')
        lon = preferences['location'].get('longitude')
        radius = preferences.get('radius', 10)  # радиус поиска в километрах
        
        if lat and lon:
            filtered_announcements = []
            for announcement in announcements:
                if announcement.latitude and announcement.longitude:
                    distance = calculate_distance(
                        float(lat), float(lon),
                        float(announcement.latitude), float(announcement.longitude)
                    )
                    if distance <= float(radius):
                        filtered_announcements.append(announcement.id)
            
            announcements = announcements.filter(id__in=filtered_announcements)
    
    # Создаем или обновляем запись о совпадениях
    match, created = Match.objects.get_or_create(user=user)
    match.set_matched_announcements([a.id for a in announcements])
    match.save()
    
    return announcements 