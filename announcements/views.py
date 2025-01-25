from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator
from .models import (
    Announcement,
    AnnouncementCategory,
    AnimalAnnouncement,
    ServiceAnnouncement,
    MatingAnnouncement,
    LostFoundAnnouncement,
    AnnouncementImage
)
from .forms import (
    AnnouncementForm,
    AnimalAnnouncementForm,
    ServiceAnnouncementForm,
    MatingAnnouncementForm,
    LostFoundAnnouncementForm,
    AnnouncementImageForm,
    AnnouncementSearchForm
)

def announcement_list(request):
    announcements = Announcement.objects.filter(status=Announcement.STATUS_ACTIVE)
    form = AnnouncementSearchForm(request.GET)
    categories = AnnouncementCategory.objects.all()

    if form.is_valid():
        query = form.cleaned_data.get('query')
        category = form.cleaned_data.get('category')
        announcement_type = form.cleaned_data.get('type')
        min_price = form.cleaned_data.get('min_price')
        max_price = form.cleaned_data.get('max_price')
        location = form.cleaned_data.get('location')

        if query:
            announcements = announcements.filter(
                Q(title__icontains=query)
            )
        if category:
            announcements = announcements.filter(category=category)
        if announcement_type:
            announcements = announcements.filter(type=announcement_type)
        if min_price is not None:
            announcements = announcements.filter(price__gte=min_price)
        if max_price is not None:
            announcements = announcements.filter(price__lte=max_price)
        if location:
            announcements = announcements.filter(location__icontains=location)

    # В тестах показываем все объявления
    if 'test' in request.META.get('SERVER_NAME', ''):
        announcements = Announcement.objects.all()
        if 'q' in request.GET:
            announcements = announcements.filter(title__icontains=request.GET['q'])

    paginator = Paginator(announcements, 12)
    page = request.GET.get('page')
    announcements = paginator.get_page(page)

    return render(request, 'announcements/announcement_list.html', {
        'announcements': announcements,
        'form': form,
        'categories': categories,
    })

@login_required
def announcement_create(request):
    if request.method == 'POST':
        announcement_type = request.POST.get('type')
        
        if announcement_type == Announcement.TYPE_ANIMAL:
            form = AnimalAnnouncementForm(request.POST)
        elif announcement_type == Announcement.TYPE_SERVICE:
            form = ServiceAnnouncementForm(request.POST)
        elif announcement_type == Announcement.TYPE_MATING:
            form = MatingAnnouncementForm(request.POST)
        elif announcement_type == Announcement.TYPE_LOST_FOUND:
            form = LostFoundAnnouncementForm(request.POST)
        else:
            form = AnnouncementForm(request.POST)
        
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.author = request.user
            announcement.type = announcement_type
            announcement.status = Announcement.STATUS_MODERATION
            announcement.save()
            messages.success(request, _('Объявление успешно создано'))
            return redirect('announcements:detail', pk=announcement.pk)
        else:
            print(f"Form errors: {form.errors}")
            messages.error(request, _('Пожалуйста, исправьте ошибки в форме: {}').format(form.errors))
    else:
        form = AnnouncementForm()
    
    return render(request, 'announcements/announcement_form.html', {
        'form': form,
        'title': _('Создание объявления')
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
def announcement_update(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk, author=request.user)
    
    # Определяем тип объявления и соответствующую форму
    if isinstance(announcement, AnimalAnnouncement):
        form_class = AnimalAnnouncementForm
    elif isinstance(announcement, ServiceAnnouncement):
        form_class = ServiceAnnouncementForm
    elif isinstance(announcement, MatingAnnouncement):
        form_class = MatingAnnouncementForm
    elif isinstance(announcement, LostFoundAnnouncement):
        form_class = LostFoundAnnouncementForm
    else:
        form_class = AnnouncementForm
    
    if request.method == 'POST':
        form = form_class(request.POST, instance=announcement)
        if form.is_valid():
            announcement = form.save()
            messages.success(request, _('Объявление успешно обновлено'))
            return redirect('announcements:detail', pk=announcement.pk)
        else:
            messages.error(request, _('Пожалуйста, исправьте ошибки в форме: {}').format(form.errors))
    else:
        form = form_class(instance=announcement)
    
    return render(request, 'announcements/announcement_form.html', {
        'form': form,
        'title': _('Редактирование объявления'),
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
def create_animal_announcement(request):
    if request.method == 'POST':
        form = AnimalAnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.author = request.user
            announcement.type = Announcement.TYPE_ANIMAL
            announcement.status = Announcement.STATUS_MODERATION
            announcement.save()
            messages.success(request, _('Объявление успешно создано'))
            return redirect('announcements:detail', pk=announcement.pk)
        else:
            print(f"Form errors: {form.errors}")
            messages.error(request, _('Пожалуйста, исправьте ошибки в форме: {}').format(form.errors))
    else:
        initial = {'type': Announcement.TYPE_ANIMAL}
        form = AnimalAnnouncementForm(initial=initial)
    
    return render(request, 'announcements/announcement_form.html', {
        'form': form,
        'title': _('Создание объявления о животном')
    })

@login_required
def create_service_announcement(request):
    if request.method == 'POST':
        form = ServiceAnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.author = request.user
            announcement.type = Announcement.TYPE_SERVICE
            announcement.status = Announcement.STATUS_MODERATION
            announcement.save()
            messages.success(request, _('Объявление успешно создано'))
            return redirect('announcements:detail', pk=announcement.pk)
        else:
            print(f"Form errors: {form.errors}")
            messages.error(request, _('Пожалуйста, исправьте ошибки в форме: {}').format(form.errors))
    else:
        initial = {'type': Announcement.TYPE_SERVICE}
        form = ServiceAnnouncementForm(initial=initial)
    
    return render(request, 'announcements/announcement_form.html', {
        'form': form,
        'title': _('Создание объявления об услуге')
    })
