from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.utils import timezone
from datetime import timedelta
from .models import Coupon  # Змініть на правильний імпорт вашої моделі

def assign_welcome_coupon():
    """Допоміжна функція створення загального купона."""
    try:
        Coupon.objects.get_or_create(
            code='WELCOME10',
            defaults={
                'discount_type': 'percent',
                'discount_value': 10,
                'valid_from': timezone.now(),
                'valid_to': timezone.now() + timedelta(days=365*5),
                'active': True,
            }
        )
    except Exception as e:
        print(f"Помилка створення купону: {e}")

class CustomAccountAdapter(DefaultAccountAdapter):
    """Спрацьовує при реєстрації через стандартну форму."""
    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit)
        assign_welcome_coupon()
        return user

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Спрацьовує при авторизації через Google (або інші соцмережі)."""
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        assign_welcome_coupon()
        return user