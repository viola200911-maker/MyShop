from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.utils import timezone

from .forms import CustomUserCreationForm, UserProfileForm, UserSecurityForm
from Cart.cart import merge_carts
from Shop.models import Coupon, UserCoupon


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            merge_carts(request)

            # 🎁 Створення / отримання привітального промокоду
            try:
                Coupon.objects.get_or_create(
                    code='WELCOME10',
                    defaults={
                        'discount_type': 'percent',
                        'discount_value': 10,
                        'valid_from': timezone.now(),
                        'valid_to': timezone.now() + timedelta(days=365*5),
                        'active': True,
                        'is_single_use': True
                    }
                )
                messages.success(request, "Успішна реєстрація! Вам доступний промокод на першу покупку 10%: WELCOME10")
            except Exception:
                messages.success(request, "Успішна реєстрація!")

            return redirect('home')
        else:
            messages.error(request, "Помилка під час реєстрації. Перевірте введені дані.")
    else:
        form = CustomUserCreationForm()

    return render(request, 'Users/register.html', {'form': form})


class UserLoginView(LoginView):
    template_name = 'Users/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        merge_carts(self.request)
        return response

    def get_success_url(self):
        return reverse_lazy('home')


@login_required
def profile_view(request):
    if request.method == "POST" and "cancel" in request.POST:
        messages.info(request, "Зміни скасовано.")
        return redirect('profile')

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            if form.has_changed():
                form.save()
                changed_fields = [form.fields[field].label for field in form.changed_data]
                messages.success(request, f"Успішно оновлено поля: {', '.join(changed_fields)}")
            else:
                messages.info(request, "Ви не внесли жодних змін.")
            return redirect('profile')
        else:
            messages.error(request, "Будь ласка, виправте помилки у формі.")
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'Users/profile.html', {'form': form})


@login_required
def security_view(request):
    if request.method == "POST":
        form = UserSecurityForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Безпекові дані (логін/email/пароль) успішно оновлено!")
            return redirect('profile')
        else:
            messages.error(request, "Не вдалося оновити дані. Перевірте помилки нижче.")
    else:
        form = UserSecurityForm(user=request.user)

    return render(request, 'Users/security.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "Ви успішно вийшли з системи.")
    return redirect('login')


def home(request):
    welcome_coupon = None

    # 1. Перевіряємо, чи користувач авторизований
    if request.user.is_authenticated:
        # 2. Шукаємо активний привітальний купон
        coupon = Coupon.objects.filter(code='WELCOME10', active=True).first()
        
        # Перевіряємо, чи купон існує і чи дійсний він по датах (через ваш метод is_valid)
        if coupon and coupon.is_valid():
            # 3. Перевіряємо, чи є запис у UserCoupon для цього користувача і купона
            has_used_coupon = UserCoupon.objects.filter(user=request.user, coupon=coupon).exists()
            
            # Якщо користувач ще не використовував купон, передаємо його в шаблон
            if not has_used_coupon:
                welcome_coupon = coupon

    context = {
        'welcome_coupon': welcome_coupon,
    }
    return render(request, 'Users/home.html', context)