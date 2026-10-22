from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q

from Shop.models import Product, Category
from Orders.models import Order
from .forms import AdminUserEditForm, AdminOrderEditForm, ProductForm

User = get_user_model()


def admin_required(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@user_passes_test(admin_required)
def admin_dashboard(request):
    """Головна панель зі статистикою"""
    total_users = User.objects.count()
    total_orders = Order.objects.count()
    total_products = Product.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()

    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:5]

    context = {
        'total_users': total_users,
        'total_orders': total_orders,
        'total_products': total_products,
        'pending_orders': pending_orders,
        'recent_orders': recent_orders,
    }
    return render(request, 'AdminPanel/dashboard.html', context)


# ==================== УПРАВЛІННЯ КОРИСТУВАЧАМИ ====================

@user_passes_test(admin_required)
def user_list(request):
    """Список усіх користувачів із пошуком та фільтрацією"""
    users = User.objects.all().order_by('-date_joined')

    query = request.GET.get('q', '').strip()
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(phone_number__icontains=query)
        )

    role = request.GET.get('role', '').strip()
    if role == 'staff':
        users = users.filter(is_staff=True)
    elif role == 'banned':
        users = users.filter(is_active=False)
    elif role == 'active':
        users = users.filter(is_active=True)

    return render(request, 'AdminPanel/user_list.html', {
        'users': users,
        'query': query,
        'role': role,
    })


@user_passes_test(admin_required)
def user_detail(request, user_id):
    """Редагування користувача, зміна прав, забанити/розбанити"""
    target_user = get_object_or_404(User, id=user_id)
    user_orders = Order.objects.filter(user=target_user)

    if request.method == 'POST':
        form = AdminUserEditForm(request.POST, instance=target_user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Дані користувача {target_user.username} оновлено!")
            return redirect('admin_panel:user_detail', user_id=target_user.id)
    else:
        form = AdminUserEditForm(instance=target_user)

    return render(request, 'AdminPanel/user_detail.html', {
        'target_user': target_user,
        'form': form,
        'user_orders': user_orders,
    })


@user_passes_test(admin_required)
def toggle_user_ban(request, user_id):
    """Швидке банення / розбанення користувача"""
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        messages.error(request, "Ви не можете забанити самого себе!")
    else:
        target_user.is_active = not target_user.is_active
        target_user.save()
        status_text = "розбанено" if target_user.is_active else "забанено"
        messages.success(request, f"Користувача {target_user.username} {status_text}!")
    return redirect('admin_panel:user_list')


# ==================== УПРАВЛІННЯ ЗАМОВЛЕННЯМИ ====================

@user_passes_test(admin_required)
def admin_order_list(request):
    """Список замовлень для адміна"""
    orders = Order.objects.all().order_by('-created_at')

    query = request.GET.get('q', '').strip()
    if query:
        orders = orders.filter(
            Q(id__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        orders = orders.filter(status=status_filter)

    return render(request, 'AdminPanel/order_list.html', {
        'orders': orders,
        'query': query,
        'status_filter': status_filter,
        'STATUS_CHOICES': Order.STATUS_CHOICES,
    })


@user_passes_test(admin_required)
def admin_order_detail(request, order_id):
    """Редагування статусу та даних замовлення"""
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        form = AdminOrderEditForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f"Замовлення №{order.id} успішно оновлено!")
            return redirect('admin_panel:admin_order_detail', order_id=order.id)
    else:
        form = AdminOrderEditForm(instance=order)

    total_cost = sum(item.price * item.quantity for item in order.items.all())

    return render(request, 'AdminPanel/order_detail.html', {
        'order': order,
        'form': form,
        'total_cost': total_cost,
    })


# ==================== УПРАВЛІННЯ ТОВАРАМИ ====================

@user_passes_test(admin_required)
def admin_product_list(request):
    """Список товарів для адміна"""
    products = Product.objects.all().select_related('category').order_by('-id')
    
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))

    return render(request, 'AdminPanel/product_list.html', {'products': products, 'query': query})


@user_passes_test(admin_required)
def product_add(request):
    """Додавання нового товару"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f"Товар '{product.name}' успішно додано!")
            return redirect('admin_panel:admin_product_list')
    else:
        form = ProductForm()

    return render(request, 'AdminPanel/product_form.html', {'form': form, 'title': 'Додати новий товар'})


@user_passes_test(admin_required)
def product_edit(request, product_id):
    """Редагування товару"""
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"Товар '{product.name}' успішно оновлено!")
            return redirect('admin_panel:admin_product_list')
    else:
        form = ProductForm(instance=product)

    return render(request, 'AdminPanel/product_form.html', {'form': form, 'title': f'Редагування товару: {product.name}'})


@user_passes_test(admin_required)
def product_delete(request, product_id):
    """Видалення товару"""
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f"Товар '{name}' видалено!")
        return redirect('admin_panel:admin_product_list')

    return render(request, 'AdminPanel/product_confirm_delete.html', {'product': product})   

from Shop.models import Review

@user_passes_test(admin_required)
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    product_slug = review.product.slug
    review.delete()
    messages.success(request, "Відгук успішно видалено.")
    return redirect('shop:product_detail', slug=product_slug)