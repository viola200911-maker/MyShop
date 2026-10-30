from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
import threading
import time

from .models import Order, OrderItem
from Shop.models import Coupon, UserCoupon
from .forms import OrderCreateForm
from Cart.cart import get_cart
from django.contrib.auth import get_user_model
import traceback


@login_required
def order_list(request):
    """Список усіх замовлень поточного користувача з пошуком та фільтрацією"""
    orders = Order.objects.filter(user=request.user)

    # 1. Пошук за ID замовлення або назвою товару
    query = request.GET.get('q', '').strip()
    if query:
        orders = orders.filter(
            Q(id__icontains=query) | 
            Q(items__product__name__icontains=query)
        ).distinct()

    # 2. Фільтрація за статусом
    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        orders = orders.filter(status=status_filter)

    # 3. Сортування за датою
    date_order = request.GET.get('date_order', 'desc')
    if date_order == 'asc':
        orders = orders.order_by('created_at')
    else:
        orders = orders.order_by('-created_at')

    return render(request, 'Orders/order_list.html', {
        'orders': orders,
        'query': query,
        'status_filter': status_filter,
        'date_order': date_order,
        'STATUS_CHOICES': Order.STATUS_CHOICES,
    })


@login_required
def order_detail(request, order_id):
    """Детальна інформація про конкретне замовлення"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    total_cost = sum(item.price * item.quantity for item in order.items.all())
    
    return render(request, 'Orders/order_detail.html', {
        'order': order,
        'total_cost': total_cost
    })


@login_required
def order_cancel_request(request, order_id):
    """Запит на скасування замовлення"""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        
        # 1. Лист для КОРИСТУВАЧА
        user_subject = f"MyShop — Запит на скасування замовлення #{order.id}"
        user_message = (
            f"Вітаємо, {order.first_name}!\n\n"
            f"Ми отримали ваш запит на скасування замовлення #{order.id}.\n"
            f"Причина скасування: {reason if reason else 'Не вказана'}.\n\n"
            f"Наш менеджер розгляне ваш запит найближчим часом та зв'яжеться з вами."
        )

        # 2. Лист для АДМІНІСТРААТОРА (менеджера)
        admin_subject = f"[УВАГА] Новий запит на скасування замовлення #{order.id}"
        admin_message = (
            f"Увага! Користувач {request.user.username} (email: {order.email}) запросив скасування замовлення #{order.id}.\n\n"
            f"Причина скасування від клієнта:\n{reason if reason else 'Причина не вказана'}\n\n"
            f"Перевірте деталі замовлення в адміністративній панелі."
        )

        try:
            # Надсилаємо лист клієнту
            send_mail(
                user_subject,
                user_message,
                settings.DEFAULT_FROM_EMAIL,
                [order.email],
                fail_silently=False,
            )
            
            # Надсилаємо окремий лист адміністратору (наприклад, на пошту магазину)
            send_mail(
                admin_subject,
                admin_message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.DEFAULT_FROM_EMAIL],  # або сюди можна вписати інший email адміна
                fail_silently=False,
            )

            messages.success(request, f"Запит на скасування замовлення #{order.id} успішно надіслано! Перевірте пошту.")
        except Exception as e:
            messages.warning(request, "Запит збережено, але виникла помилка під час надсилання електронного листа.")

        return redirect('orders:order_detail', order_id=order_id)

    return render(request, 'Orders/order_cancel_confirm.html', {'order': order})




@login_required # або якщо у тебе оформлення доступне і для неавторизованих, дивись по своєму декоратору
def order_create(request):
    cart = get_cart(request)
    if len(cart) == 0:
        return redirect('shop:product_list')

    # Формуємо початкові дані для користувача (якщо він залогінений)
    initial_data = {}
    if request.user.is_authenticated:
        user = request.user
        initial_data = {
            'first_name': getattr(user, 'first_name', ''),
            'last_name': getattr(user, 'last_name', ''),
            'email': getattr(user, 'email', ''),
            'phone': getattr(user, 'phone_number', getattr(user, 'phone', '')),
            'address': getattr(user, 'address', ''),
        }

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        
        if form.is_valid():
            # 1. ПЕРЕВІРКА СКЛАДУ: перевіряємо чи вистачає всіх товарів у кошику ДО збереження замовлення
            for item in cart:
                product = item['product']
                quantity = item['quantity']
                if product.stock < quantity:
                    messages.error(
                        request, 
                        f"Вибачте, товару '{product.name}' забагато в кошику. На складі залишилось лише {product.stock} шт."
                    )
                    return redirect('cart:cart_detail')

            order = form.save(commit=False)
            
            if request.user.is_authenticated:
                order.user = request.user
                
                # Якщо стоїть прапорець "is_default" — оновлюємо дані профілю
                if form.cleaned_data.get('is_default'):
                    new_email = form.cleaned_data.get('email')
                    
                    if new_email and new_email != user.email:
                        User = get_user_model()
                        if not User.objects.filter(email__iexact=new_email).exclude(id=user.id).exists():
                            user.email = new_email

                    user.first_name = form.cleaned_data.get('first_name')
                    user.last_name = form.cleaned_data.get('last_name')
                    if hasattr(user, 'phone_number'):
                        user.phone_number = form.cleaned_data.get('phone')
                    if hasattr(user, 'address'):
                        user.address = form.cleaned_data.get('address')
                        
                    user.save()

            # Зберігаємо замовлення у базі даних
            order.save()

            # Обробка використаного купона
            coupon_id = request.session.get('coupon_id')
            if coupon_id:
                try:
                    coupon = Coupon.objects.get(id=coupon_id)
                    if request.user.is_authenticated and coupon.is_single_use:
                        UserCoupon.objects.create(user=request.user, coupon=coupon)
                    del request.session['coupon_id']
                except Coupon.DoesNotExist:
                    pass

            # Збереження товарів замовлення та ОНОВЛЕННЯ СКЛАДУ
            for item in cart:
                product = item['product']
                quantity = item['quantity']
                
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=item['price'],
                    quantity=quantity
                )
                
                # 2. Зменшуємо сток та деактивуємо товар, якщо залишок 0 або менше
                product.stock -= quantity
                if product.stock <= 0:
                    product.stock = 0
                    product.is_active = False  # Товар стає неактивним
                product.save()

            # Очищення кошика
            cart.clear()

            # Асинхронна відправка email про замовлення
            if order.email:
                subject = f"MyShop — Підтвердження замовлення №{order.id}"
                message = (
                    f"Вітаємо, {order.first_name}!\n\n"
                    f"Дякуємо за ваше замовлення №{order.id}.\n"
                    f"Адреса доставки: {order.address}\n\n"
                    f"Ми зв'яжемося з вами найближчим часом для підтвердження."
                )

                # Запускаємо відправку email в окремому daemon-потоці
                email_thread = threading.Thread(
                    target=send_order_email,
                    args=(subject, message, order.email),
                    daemon=True 
                )
                email_thread.start()

            return redirect('orders:order_success', order_id=order.id)
        
    else:
        # Для звичайного GET-запиту створюємо форму з початковими даними профілю
        form = OrderCreateForm(initial=initial_data)

    return render(request, 'Orders/checkout.html', {
        'cart': cart,
        'form': form
    })


def send_order_email(subject, message, recipient):
    """Функція для асинхронної відправки email з retry логікою"""
    max_retries = 3
    retry_delay = 2  # секунди між спробами

    for attempt in range(max_retries):
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [recipient],
                fail_silently=True,
            )
            print(f"Email успішно надіслано на {recipient} (спроба {attempt + 1})")
            return
        except Exception as e:
            print(f"ПОМИЛКА відправки email на {recipient} (спроба {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                print(f"Не вдалося надіслати email на {recipient} після {max_retries} спроб")
                traceback.print_exc()


def order_success(request, order_id):
    """Сторінка успішного оформлення замовлення"""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'Orders/order_success.html', {'order': order})


@login_required
def order_reorder(request, order_id):
    """Повтор замовлення"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    cart = get_cart(request)

    added_count = 0
    for item in order.items.all():
        is_available = getattr(item.product, 'available', getattr(item.product, 'is_active', True))
        
        if item.product and is_available:
            cart.add(
                product=item.product, 
                quantity=item.quantity, 
                update_quantity=False
            )
            added_count += 1

    if added_count > 0:
        messages.success(request, f"Товари з замовлення №{order.id} додано до вашого кошика!")
        return redirect('cart:cart_detail')
    else:
        messages.error(request, "На жаль, жоден з товарів цього замовлення зараз недоступний для покупки.")
        return redirect('orders:order_detail', order_id=order.id)
