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
                Q(title__icontains=query) |
                Q(description__icontains=query)
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
