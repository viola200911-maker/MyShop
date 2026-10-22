from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone

from Shop.models import Product, Coupon, UserCoupon
from .cart import get_cart


def cart_detail(request):
    cart = get_cart(request)
    now = timezone.now().date()

    # 🎂 Автоматична перевірка Дня народження (активна знижка навколо ДН)
    if request.user.is_authenticated and getattr(request.user, 'date_of_birth', None):
        user_dob = request.user.date_of_birth
        if user_dob.month == now.month and abs(user_dob.day - now.day) <= 3:
            bday_coupon, _ = Coupon.objects.get_or_create(
                code=f"BDAY-{request.user.id}",
                defaults={
                    'discount_type': 'percent',
                    'discount_value': 15,
                    'valid_from': timezone.now() - timezone.timedelta(days=3),
                    'valid_to': timezone.now() + timezone.timedelta(days=4),
                    'active': True,
                    'is_auto_birthday': True
                }
            )
            if not UserCoupon.objects.filter(user=request.user, coupon=bday_coupon).exists():
                request.session['coupon_id'] = bday_coupon.id
                messages.info(request, "🎂 З Днем народження! Вам автоматично застосовано святкову знижку 15%!")

    return render(request, 'Cart/detail.html', {
        'cart': cart,
        'coupon_id': request.session.get('coupon_id')
    })


def apply_coupon(request):
    """View для введення промокоду вручну"""
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        now = timezone.now()

        try:
            coupon = Coupon.objects.get(code__iexact=code, valid_from__lte=now, valid_to__gte=now, active=True)
            
            if coupon.is_single_use and request.user.is_authenticated:
                if UserCoupon.objects.filter(user=request.user, coupon=coupon).exists():
                    messages.error(request, "Ви вже використали цей промокод раніше!")
                    return redirect('cart:cart_detail')

            request.session['coupon_id'] = coupon.id
            messages.success(request, f"Промокод '{coupon.code}' успішно застосовано!")
        except Coupon.DoesNotExist:
            messages.error(request, "Недійсний або застарілий промокод.")

    return redirect('cart:cart_detail')


@require_POST
def cart_add(request, product_id):
    """Додати товар у кошик"""
    cart = get_cart(request)
    product = get_object_or_404(Product, id=product_id)
    
    if hasattr(product, 'is_active') and not product.is_active:
        messages.error(request, f'Товар "{product.name}" недоступний для покупки')
        return redirect('shop:product_detail', slug=product.slug)
    
    quantity = int(request.POST.get('quantity', 1))
    
    if hasattr(product, 'stock') and quantity > product.stock:
        messages.error(request, f'Доступно тільки {product.stock} од. товару "{product.name}"')
        return redirect('shop:product_detail', slug=product.slug)
    
    cart.add(product=product, quantity=quantity)
    messages.success(request, f'Товар "{product.name}" додано до кошика')
    return redirect('cart:cart_detail')


@require_POST
def cart_remove(request, product_id):
    """Видалити товар з кошика"""
    cart = get_cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    
    messages.success(request, f'Товар "{product.name}" видалено з кошика')
    return redirect('cart:cart_detail')


@require_POST
def cart_update(request, product_id):
    """Оновлення кількості товару"""
    cart = get_cart(request)
    product = get_object_or_404(Product, id=product_id)
    action = request.POST.get('action')
    
    current_quantity = 0
    for item in cart:
        if str(item['product'].id) == str(product.id):
            current_quantity = item['quantity']
            break

    if action == 'increase':
        new_quantity = current_quantity + 1
    elif action == 'decrease':
        new_quantity = current_quantity - 1
    else:
        new_quantity = int(request.POST.get('quantity', 1))

    if hasattr(product, 'stock') and new_quantity > product.stock:
        messages.error(request, f'Максимально доступно {product.stock} од. товару "{product.name}"')
        return redirect('cart:cart_detail')

    if new_quantity > 0:
        cart.add(product=product, quantity=new_quantity, update_quantity=True)
    else:
        cart.remove(product)
        messages.info(request, f'Товар "{product.name}" видалено з кошика')

    return redirect('cart:cart_detail')

@require_POST
def cart_clear(request):
    """Повне очищення кошика"""
    cart = get_cart(request)
    cart.clear()
    
    # Видаляємо купон із сесії, якщо він був застосований
    if 'coupon_id' in request.session:
        del request.session['coupon_id']
        
    messages.info(request, "Ваш кошик повністю очищено.")
    return redirect('cart:cart_detail')