from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Exists, OuterRef
from catalog.models import Product
from .models import Swipe, SwipeHistory
from login_auth.models import SellerVerification
from chat.models import Dialog

@login_required
def swipe_view(request):
    # Get products that haven't been swiped by the user yet
    swiped_products = Swipe.objects.filter(
        user=request.user,
        product=OuterRef('pk')
    )
    
    products = Product.objects.filter(
        Q(status='active') &
        ~Q(seller=request.user) &
        ~Exists(swiped_products)
    ).select_related('seller', 'category').prefetch_related('images')[:10]

    return render(request, 'kotopsinder/swipe.html', {
        'products': products
    })

@login_required
def record_swipe(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    product_id = request.POST.get('product_id')
    direction = request.POST.get('direction')
    
    if not product_id or direction not in [Swipe.LIKE, Swipe.DISLIKE]:
        return JsonResponse({'error': 'Invalid parameters'}, status=400)
    
    product = get_object_or_404(Product, id=product_id, status='active')
    
    # Record the swipe
    swipe, created = Swipe.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={'direction': direction}
    )
    
    # If not created, update the direction
    if not created:
        swipe.direction = direction
        swipe.save()
    
    # Record in history
    SwipeHistory.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    response_data = {
        'status': 'success',
        'direction': direction
    }
    
    # If it's a like, include chat info in response
    if direction == Swipe.LIKE:
        dialog = Dialog.objects.filter(
            participants=request.user
        ).filter(
            participants=product.seller
        ).first()
        if dialog:
            response_data['chat_url'] = dialog.get_absolute_url()
    
    return JsonResponse(response_data)

@login_required
def undo_last_swipe(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    # Get the last swipe
    last_swipe = Swipe.objects.filter(user=request.user).order_by('-created_at').first()
    
    if not last_swipe:
        return JsonResponse({'error': 'No swipes to undo'}, status=400)
    
    # Delete the swipe and its history
    last_swipe.delete()
    SwipeHistory.objects.filter(user=request.user, product=last_swipe.product).delete()
    
    return JsonResponse({'status': 'success'})

@login_required
def get_next_cards(request):
    """API endpoint to get next batch of cards"""
    swiped_products = Swipe.objects.filter(
        user=request.user,
        product=OuterRef('pk')
    )
    
    products = Product.objects.filter(
        Q(status='active') &
        ~Q(seller=request.user) &
        ~Exists(swiped_products)
    ).select_related('seller', 'category').prefetch_related('images')[:5]
    
    cards_data = []
    for product in products:
        seller_verification = SellerVerification.objects.filter(
            user=product.seller,
            status='approved'
        ).exists()
        
        cards_data.append({
            'id': product.id,
            'title': product.title,
            'price': str(product.price),
            'description': product.description,
            'location': product.location,
            'image_url': product.images.first().image.url if product.images.exists() else None,
            'seller_name': product.seller.get_full_name(),
            'seller_verified': seller_verification,
            'category_name': product.category.name,
        })
    
    return JsonResponse({'cards': cards_data}) 