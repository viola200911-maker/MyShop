# Cart/signals.py
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .cart import merge_carts

@receiver(user_logged_in)
def auto_merge_carts_on_login(sender, request, user, **kwargs):
    """Автоматично об'єднує кошики при БУДЬ-ЯКОМУ логіні (включаючи Google OAuth)"""
    merge_carts(request)