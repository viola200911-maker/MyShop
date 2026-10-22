# Shop/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from .models import Product, Category
from .forms import ReviewForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def product_list_view(request, category_slug=None):
    category = None
    products = Product.objects.filter(is_active=True).select_related('category')

    # 1. Фільтрація за категорією
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(Q(category=category) | Q(category__parent=category))

    # 2. Отримання фільтрів з GET-запиту
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    in_stock = request.GET.get('in_stock')
    ordering = request.GET.get('ordering')

    # Фільтрація за ціною
    if price_min:
        try:
            products = products.filter(price__gte=float(price_min))
        except ValueError:
            pass

    if price_max:
        try:
            products = products.filter(price__lte=float(price_max))
        except ValueError:
            pass

    # Фільтрація за наявністю
    if in_stock == '1':
        products = products.filter(stock__gt=0)

    # 3. Сортування
    if ordering == 'price_asc':
        products = products.order_by('price')
    elif ordering == 'price_desc':
        products = products.order_by('-price')
    elif ordering == 'name_asc':
        products = products.order_by('name')
    elif ordering == 'newest':
        products = products.order_by('-created_at') if hasattr(Product, 'created_at') else products.order_by('-id')

    context = {
        'category': category,
        'products': products,
        'price_min': price_min or '',
        'price_max': price_max or '',
        'in_stock': in_stock or '',
        'ordering': ordering or '',
    }
    return render(request, 'Shop/product_list.html', context)


def search_prod(request):
    search_query = request.GET.get('q', '').strip()
    products = Product.objects.filter(is_active=True).select_related('category')
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    else:
        products = Product.objects.none()

    # Отримання додаткових фільтрів для результатів пошуку
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    in_stock = request.GET.get('in_stock')
    ordering = request.GET.get('ordering')

    if price_min:
        try:
            products = products.filter(price__gte=float(price_min))
        except ValueError:
            pass

    if price_max:
        try:
            products = products.filter(price__lte=float(price_max))
        except ValueError:
            pass

    if in_stock == '1':
        products = products.filter(stock__gt=0)

    if ordering == 'price_asc':
        products = products.order_by('price')
    elif ordering == 'price_desc':
        products = products.order_by('-price')
    elif ordering == 'name_asc':
        products = products.order_by('name')

    context = {
        'products': products,
        'search_query': search_query,
        'price_min': price_min or '',
        'price_max': price_max or '',
        'in_stock': in_stock or '',
        'ordering': ordering or '',
    }
    return render(request, 'Shop/product_list.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    reviews = product.reviews.all()
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "Будь ласка, увійдіть в акаунт, щоб залишити відгук.")
            return redirect('login')

        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, "Дякуємо! Ваш відгук успішно додано.")
            return redirect('shop:product_detail', slug=product.slug)
    else:
        form = ReviewForm()

    return render(request, 'Shop/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'form': form,
        'avg_rating': product.get_average_rating(),
    })