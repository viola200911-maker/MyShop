from django.utils import timezone
from datetime import timedelta
from .models import Coupon  # або ваша модель бонуса/промокоду

def give_welcome_bonus(user):
    """Видає вітальний бонус новому користувачу"""
    try:
        coupon, created = Coupon.objects.get_or_create(
            code='WELCOME10',
            defaults={
                'discount_type': 'percent',
                'discount_value': 10,
                'valid_from': timezone.now(),
                'valid_to': timezone.now() + timedelta(days=365*5),
                'active': True,
                'is_single_use': True,
            }
        )
        # Якщо у вас зв'язок ManyToMany або окрема таблиця для користувачів та їх промокодів, 
        # додайте користувача до списку тих, хто отримав бонус:
        # coupon.users.add(user)
    except Exception as e:
        print(f"Помилка при створенні бонусу: {e}")