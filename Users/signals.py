from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from Shop.models import Coupon  # Змініть імпорт, якщо Coupon знаходиться в іншому додатку
from allauth.account.signals import user_signed_up
from .views import give_welcome_bonus  # або імпортуйте звідки винесли функцію

@receiver(user_signed_up)
def social_signup_bonus(request, user, **kwargs):
    # Цей код виконається лише при першій реєстрації через Google/соцмережі
    give_welcome_bonus(user)