from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from Shop.models import Coupon  # Змініть імпорт, якщо Coupon знаходиться в іншому додатку

User = get_user_model()

@receiver(post_save, sender=User)
def create_welcome_coupon_on_register(sender, instance, created, **kwargs):
    # created = True означає, що це новий запис, а не оновлення існуючого
    if created: 
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