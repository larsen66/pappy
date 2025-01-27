from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from .models import (
    Announcement,
    AnnouncementCategory,
    AnimalAnnouncement,
    ServiceAnnouncement,
    MatingAnnouncement,
    LostFoundAnnouncement,
    AnnouncementImage,
    LostPet
)
from .forms import (
    AnnouncementForm,
    AnimalAnnouncementForm,
    ServiceAnnouncementForm,
    MatingAnnouncementForm,
    LostFoundAnnouncementForm,
    AnnouncementImageForm,
    AnnouncementSearchForm,
    LostPetForm
)
from .filters import AnnouncementFilter
from django.conf import settings

def announcement_list(request):
    # Базовый queryset
    announcements = Announcement.objects.filter(status=Announcement.STATUS_ACTIVE)
    
    # Применяем фильтры
    announcement_filter = AnnouncementFilter(request.GET, queryset=announcements)
    announcements = announcement_filter.qs
    
    # Сортировка
    sort_by = request.GET.get('sort')
    if sort_by:
        if sort_by == 'price_asc':
            announcements = announcements.order_by('price')
        elif sort_by == 'price_desc':
            announcements = announcements.order_by('-price')
        elif sort_by == 'date_desc':
            announcements = announcements.order_by('-created_at')
        elif sort_by == 'date_asc':
            announcements = announcements.order_by('created_at')
        elif sort_by == 'popular':
            announcements = announcements.annotate(
                avg_rating=Avg('reviews__rating'),
                view_count=Count('views')
            ).order_by('-avg_rating', '-view_count')
    else:
        # По умолчанию сортируем по дате создания (сначала новые)
        announcements = announcements.order_by('-created_at')
    
    # Поиск по параметрам
    search_form = AnnouncementSearchForm(request.GET)
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('query')
        if search_query:
            announcements = announcements.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(animalannouncement__breed__icontains=search_query) |
                Q(serviceannouncement__service_type__icontains=search_query) |
                Q(location__icontains=search_query)
            ).distinct()
    
    # Пагинация
    paginator = Paginator(announcements, 12)
    page = request.GET.get('page')
    announcements = paginator.get_page(page)
    
    # Получаем все категории для фильтров
    categories = AnnouncementCategory.objects.all()
    
    context = {
        'announcements': announcements,
        'filter': announcement_filter,
        'form': search_form,
        'categories': categories,
        'current_sort': sort_by,
    }
    
    return render(request, 'announcements/announcement_list.html', context)

@login_required
def announcement_create(request):
    if request.method == 'POST':
        announcement_form = AnnouncementForm(request.POST)
        image_form = AnnouncementImageForm(request.POST, request.FILES)
        
        type_form = None
        announcement_type = request.POST.get('type')
        
        if announcement_type == Announcement.TYPE_ANIMAL:
            type_form = AnimalAnnouncementForm(request.POST)
        elif announcement_type == Announcement.TYPE_SERVICE:
            type_form = ServiceAnnouncementForm(request.POST)
        elif announcement_type == Announcement.TYPE_MATING:
            type_form = MatingAnnouncementForm(request.POST)
        elif announcement_type == Announcement.TYPE_LOST_FOUND:
            type_form = LostFoundAnnouncementForm(request.POST)
        
        if announcement_form.is_valid() and type_form and type_form.is_valid() and image_form.is_valid():
            announcement = announcement_form.save(commit=False)
            announcement.author = request.user
            announcement.save()
            
            type_instance = type_form.save(commit=False)
            type_instance.announcement = announcement
            type_instance.save()
            
            if image_form.cleaned_data.get('image'):
                image = image_form.save(commit=False)
                image.announcement = announcement
                image.save()
            
            messages.success(request, _('Объявление успешно создано'))
            return redirect('announcements:detail', pk=announcement.pk)
    else:
        announcement_form = AnnouncementForm()
        image_form = AnnouncementImageForm()
    
    return render(request, 'announcements/announcement_form.html', {
        'announcement_form': announcement_form,
        'image_form': image_form,
        'animal_form': AnimalAnnouncementForm(),
        'service_form': ServiceAnnouncementForm(),
        'mating_form': MatingAnnouncementForm(),
        'lost_found_form': LostFoundAnnouncementForm(),
    })

def announcement_detail(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    announcement.views_count += 1
    announcement.save()
    
    type_details = None
    if announcement.type == Announcement.TYPE_ANIMAL:
        type_details = announcement.animal_details
    elif announcement.type == Announcement.TYPE_SERVICE:
        type_details = announcement.service_details
    elif announcement.type == Announcement.TYPE_MATING:
        type_details = announcement.mating_details
    elif announcement.type == Announcement.TYPE_LOST_FOUND:
        type_details = announcement.lost_found_details
    
    return render(request, 'announcements/announcement_detail.html', {
        'announcement': announcement,
        'type_details': type_details,
    })

@login_required
def announcement_edit(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk, author=request.user)
    
    if request.method == 'POST':
        announcement_form = AnnouncementForm(request.POST, instance=announcement)
        image_form = AnnouncementImageForm(request.POST, request.FILES)
        
        type_form = None
        if announcement.type == Announcement.TYPE_ANIMAL:
            type_form = AnimalAnnouncementForm(request.POST, instance=announcement.animal_details)
        elif announcement.type == Announcement.TYPE_SERVICE:
            type_form = ServiceAnnouncementForm(request.POST, instance=announcement.service_details)
        elif announcement.type == Announcement.TYPE_MATING:
            type_form = MatingAnnouncementForm(request.POST, instance=announcement.mating_details)
        elif announcement.type == Announcement.TYPE_LOST_FOUND:
            type_form = LostFoundAnnouncementForm(request.POST, instance=announcement.lost_found_details)
        
        if announcement_form.is_valid() and type_form and type_form.is_valid():
            announcement = announcement_form.save()
            type_form.save()
            
            if image_form.is_valid() and image_form.cleaned_data.get('image'):
                image = image_form.save(commit=False)
                image.announcement = announcement
                image.save()
            
            messages.success(request, _('Объявление успешно обновлено'))
            return redirect('announcements:detail', pk=announcement.pk)
    else:
        announcement_form = AnnouncementForm(instance=announcement)
        image_form = AnnouncementImageForm()
        
        type_form = None
        if announcement.type == Announcement.TYPE_ANIMAL:
            type_form = AnimalAnnouncementForm(instance=announcement.animal_details)
        elif announcement.type == Announcement.TYPE_SERVICE:
            type_form = ServiceAnnouncementForm(instance=announcement.service_details)
        elif announcement.type == Announcement.TYPE_MATING:
            type_form = MatingAnnouncementForm(instance=announcement.mating_details)
        elif announcement.type == Announcement.TYPE_LOST_FOUND:
            type_form = LostFoundAnnouncementForm(instance=announcement.lost_found_details)
    
    return render(request, 'announcements/announcement_form.html', {
        'announcement_form': announcement_form,
        'image_form': image_form,
        'type_form': type_form,
        'announcement': announcement,
    })

@login_required
def announcement_delete(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk, author=request.user)
    
    if request.method == 'POST':
        announcement.delete()
        messages.success(request, _('Объявление успешно удалено'))
        return redirect('announcements:list')
    
    return render(request, 'announcements/announcement_confirm_delete.html', {
        'announcement': announcement,
    })

@login_required
def my_announcements(request):
    announcements = Announcement.objects.filter(author=request.user)
    status = request.GET.get('status')
    
    if status:
        announcements = announcements.filter(status=status)
    
    paginator = Paginator(announcements, 12)
    page = request.GET.get('page')
    announcements = paginator.get_page(page)
    
    return render(request, 'announcements/my_announcements.html', {
        'announcements': announcements,
    })

@login_required
def lost_pet_create(request):
    if request.method == 'POST':
        form = LostPetForm(request.POST)
        image_form = AnnouncementImageForm(request.POST, request.FILES)
        
        if form.is_valid() and image_form.is_valid():
            with transaction.atomic():
                # Создаем базовое объявление
                announcement = Announcement.objects.create(
                    title=f"{form.cleaned_data['status']} {form.cleaned_data['pet_type']}",
                    description=form.cleaned_data['distinctive_features'],
                    type=Announcement.TYPE_LOST_FOUND,
                    author=request.user,
                    location=form.cleaned_data['last_seen_address']
                )
                
                # Создаем запись о потерянном животном
                lost_pet = form.save(commit=False)
                lost_pet.announcement = announcement
                lost_pet.save()
                
                # Сохраняем изображения
                if image_form.cleaned_data.get('image'):
                    image = image_form.save(commit=False)
                    image.announcement = announcement
                    image.save()
                
                # Отправляем уведомления пользователям в радиусе
                notify_users_in_radius(lost_pet)
                
                messages.success(request, _('Объявление успешно создано'))
                return redirect('announcements:lost_pet_detail', pk=lost_pet.pk)
    else:
        form = LostPetForm()
        image_form = AnnouncementImageForm()
    
    return render(request, 'announcements/lost_pet_form.html', {
        'form': form,
        'image_form': image_form,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    })

def lost_pet_detail(request, pk):
    lost_pet = get_object_or_404(LostPet, pk=pk)
    lost_pet.views_count += 1
    lost_pet.save()
    
    # Получаем похожие случаи
    similar_cases = lost_pet.get_similar_cases()
    
    return render(request, 'announcements/lost_pet_detail.html', {
        'lost_pet': lost_pet,
        'similar_cases': similar_cases,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    })

def lost_pets_map(request):
    """Карта всех потерянных и найденных животных"""
    lost_pets = LostPet.objects.filter(is_active=True)
    
    # Фильтрация
    status = request.GET.get('status')
    pet_type = request.GET.get('pet_type')
    days = request.GET.get('days')
    
    if status:
        lost_pets = lost_pets.filter(status=status)
    if pet_type:
        lost_pets = lost_pets.filter(pet_type=pet_type)
    if days:
        date_from = timezone.now() - timezone.timedelta(days=int(days))
        lost_pets = lost_pets.filter(date_lost_found__gte=date_from)
    
    return render(request, 'announcements/lost_pets_map.html', {
        'lost_pets': lost_pets,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    })

def notify_users_in_radius(lost_pet):
    """Отправка уведомлений пользователям в радиусе"""
    from notifications.models import Notification
    from django.contrib.auth import get_user_model
    from django.contrib.gis.measure import D
    
    User = get_user_model()
    
    # Находим пользователей в радиусе
    users_in_radius = User.objects.filter(
        profile__location__distance_lte=(
            lost_pet.last_seen_location,
            D(km=lost_pet.search_radius)
        )
    ).exclude(id=lost_pet.announcement.author.id)
    
    # Создаем уведомления
    notifications = []
    for user in users_in_radius:
        notifications.append(
            Notification(
                recipient=user,
                verb='new_lost_pet',
                action_object=lost_pet,
                description=f"Новое объявление о {'потерянном' if lost_pet.status == 'lost' else 'найденном'} животном в вашем районе"
            )
        )
    
    if notifications:
        Notification.objects.bulk_create(notifications)
        
    # Отправляем push-уведомления
    from notifications.services import send_push_notification
    for user in users_in_radius:
        if user.profile.push_enabled:
            send_push_notification(
                user,
                title="Новое объявление поблизости",
                body=f"{'Потерялось' if lost_pet.status == 'lost' else 'Найдено'} животное в вашем районе",
                data={'lost_pet_id': lost_pet.id}
            )

@login_required
def mating_create(request):
    """Create a new mating announcement"""
    if request.method == 'POST':
        form = MatingAnnouncementForm(request.POST, request.FILES)
        image_form = AnnouncementImageForm(request.POST, request.FILES)
        
        if form.is_valid() and image_form.is_valid():
            with transaction.atomic():
                # Create base announcement
                announcement = Announcement.objects.create(
                    title=f"Вязка: {form.cleaned_data['animal'].breed}",
                    description=form.cleaned_data['mating_conditions'],
                    type=Announcement.TYPE_MATING,
                    author=request.user,
                    price=form.cleaned_data.get('price_policy'),
                    status=Announcement.STATUS_MODERATION
                )
                
                # Create mating announcement
                mating = form.save(commit=False)
                mating.announcement = announcement
                mating.save()
                
                # Save images
                if image_form.cleaned_data.get('image'):
                    image = image_form.save(commit=False)
                    image.announcement = announcement
                    image.save()
                
                messages.success(request, _('Объявление о вязке создано и отправлено на модерацию'))
                return redirect('announcements:mating_detail', pk=mating.pk)
    else:
        form = MatingAnnouncementForm()
        image_form = AnnouncementImageForm()
    
    return render(request, 'announcements/mating_form.html', {
        'form': form,
        'image_form': image_form,
    })

def mating_detail(request, pk):
    """View mating announcement details"""
    mating = get_object_or_404(MatingAnnouncement, pk=pk)
    matching_partners = mating.get_matching_partners() if request.user == mating.announcement.author else None
    
    return render(request, 'announcements/mating_detail.html', {
        'mating': mating,
        'matching_partners': matching_partners,
    })

@login_required
def mating_list(request):
    """List all mating announcements with filters"""
    announcements = MatingAnnouncement.objects.filter(
        announcement__status=Announcement.STATUS_ACTIVE,
        is_available=True
    )
    
    # Apply filters
    species = request.GET.get('species')
    breed = request.GET.get('breed')
    gender = request.GET.get('gender')
    has_medical = request.GET.get('has_medical')
    
    if species:
        announcements = announcements.filter(animal__species=species)
    if breed:
        announcements = announcements.filter(animal__breed=breed)
    if gender:
        announcements = announcements.filter(animal__gender=gender)
    if has_medical:
        announcements = announcements.filter(has_medical_exam=True)
    
    # Sort options
    sort = request.GET.get('sort')
    if sort == 'age_asc':
        announcements = announcements.order_by('animal__age')
    elif sort == 'age_desc':
        announcements = announcements.order_by('-animal__age')
    elif sort == 'success':
        announcements = announcements.order_by('-successful_matings')
    else:
        announcements = announcements.order_by('-announcement__created_at')
    
    # Pagination
    paginator = Paginator(announcements, 12)
    page = request.GET.get('page')
    announcements = paginator.get_page(page)
    
    return render(request, 'announcements/mating_list.html', {
        'announcements': announcements,
        'current_filters': {
            'species': species,
            'breed': breed,
            'gender': gender,
            'has_medical': has_medical,
            'sort': sort,
        }
    })

@login_required
def mating_update(request, pk):
    """Update existing mating announcement"""
    mating = get_object_or_404(MatingAnnouncement, pk=pk, announcement__author=request.user)
    
    if request.method == 'POST':
        form = MatingAnnouncementForm(request.POST, request.FILES, instance=mating)
        if form.is_valid():
            with transaction.atomic():
                mating = form.save()
                mating.announcement.title = f"Вязка: {mating.animal.breed}"
                mating.announcement.description = form.cleaned_data['mating_conditions']
                mating.announcement.price = form.cleaned_data.get('price_policy')
                mating.announcement.save()
                
                messages.success(request, _('Объявление о вязке обновлено'))
                return redirect('announcements:mating_detail', pk=mating.pk)
    else:
        form = MatingAnnouncementForm(instance=mating)
    
    return render(request, 'announcements/mating_form.html', {
        'form': form,
        'mating': mating,
        'is_update': True,
    })
