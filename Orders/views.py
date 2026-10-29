from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q

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
        
        subject = f"MyShop — Запит на скасування замовлення №{order.id}"
        message = (
            f"Вітаємо, {order.first_name}!\n\n"
            f"Ми отримали ваш запит на скасування замовлення №{order.id}.\n"
            f"Причина скасування: {reason if reason else 'Не вказана'}.\n\n"
            f"Наш менеджер розгляне ваш запит найближчим часом та зв'яжеться з вами."
        )
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [order.email, settings.DEFAULT_FROM_EMAIL],
                fail_silently=True
            )
            messages.success(request, f"Запит на скасування замовлення №{order.id} успішно надіслано! Перевірте пошту.")
        except Exception:
            messages.warning(request, "Запит збережено, але виникла помилка під час надсилання електронного листа.")

        return redirect('orders:order_detail', order_id=order.id)

    return render(request, 'Orders/order_cancel_confirm.html', {'order': order})


import threading


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

            # Збереження товарів замовлення
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    price=item['price'],
                    quantity=item['quantity']
                )

            # Очищення кошика
            cart.clear()

            # Відправка електронного листа
            subject = f'MyShop — Підтвердження замовлення №{order.id}'
            message = (
                f"Вітаємо, {order.first_name}!\n\n"
                f"Дякуємо за ваше замовлення №{order.id}.\n"
                f"Адреса доставки: {order.address}\n\n"
                f"Ми зв'яжемося з вами найближчим часом для підтвердження."
            )
            recipient = order.email

            # Функція, яка буде працювати у фоні

            def send_order_email(sub, msg, rec):
                try:
                    send_mail(
                        sub,
                        msg,
                        settings.DEFAULT_FROM_EMAIL,
                        [rec],
                        fail_silently=False,
                    )
                    print("Email sent successfully!")
                except Exception as e:
                    print("--- ПОМИЛКА ВІДПРАВКИ ЛИСТА ---")
                    traceback.print_exc()

            # Запускаємо фоновий потік
            email_thread = threading.Thread(
                target=send_order_email, 
                args=(subject, message, recipient)
            )
            email_thread.start()

            return redirect('orders:order_success', order_id=order.id)
        
        # Якщо форма НЕ валідна (POST-запит з помилками), 
        # змінна 'form' вже містить помилки, тому ми просто провалимось нижче до render()
    
    else:
        # Для звичайного GET-запиту створюємо форму з початковими даними профілю
        form = OrderCreateForm(initial=initial_data)

    return render(request, 'Orders/checkout.html', {
        'cart': cart,
        'form': form
    })

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
