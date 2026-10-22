from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class Coupon(models.Model):
    DISCOUNT_TYPES = [
        ('percent', 'У відсотках (%)'),
        ('fixed', 'Фіксована сума (грн)'),
    ]

    code = models.CharField(max_length=50, unique=True, verbose_name="Промокод (код)")
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES, default='percent', verbose_name="Тип знижки")
    discount_value = models.DecimalField(
        max_digits=10, decimal_places=2, 
        verbose_name="Значення знижки (% або грн)",
        validators=[MinValueValidator(0)]
    )
    valid_from = models.DateTimeField(verbose_name="Дійсний з")
    valid_to = models.DateTimeField(verbose_name="Дійсний до")
    active = models.BooleanField(default=True, verbose_name="Активний")
    
    # Спеціальні прапорці
    is_auto_birthday = models.BooleanField(default=False, verbose_name="Авто-знижка на День народження")
    is_auto_holiday = models.BooleanField(default=False, verbose_name="Авто-знижка на свята (для всіх)")
    is_single_use = models.BooleanField(default=True, verbose_name="Одноразовий для кожного юзера")

    class Meta:
        verbose_name = "Купон / Промокод"
        verbose_name_plural = "Купони та Промокоди"

    def __str__(self):
        return f"{self.code} (-{self.discount_value}{'%' if self.discount_type == 'percent' else 'грн'})"

    def is_valid(self):
        now = timezone.now()
        return self.active and self.valid_from <= now <= self.valid_to


class UserCoupon(models.Model):
    """Таблиця для відстеження використаних або персональних купонів користувача"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='used_coupons')
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата використання")

    class Meta:
        unique_together = ('user', 'coupon')
        verbose_name = "Використаний купон користувача"
        verbose_name_plural = "Використані купони користувачів"

class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name="Назва категорії")
    slug = models.SlugField(max_length=255, unique=True, verbose_name="Slug")
    description = models.TextField(blank=True, null=True, verbose_name="Опис")
    
    # Зв'язок на саму себе: якщо parent порожній — це головна категорія,
    # якщо вказаний — це підкатегорія.
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Батьківська категорія"
    )

    class Meta:
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"
        ordering = ['name']

    def __str__(self):
        # В адмінці підкатегорії будуть показуватися як "Електроніка -> Смартфони"
        if self.parent:
            return f"{self.parent.name} -> {self.name}"
        return self.name

from django.db import models


class Product(models.Model):
    category = models.ForeignKey(
        Category, 
        related_name='products', 
        on_delete=models.CASCADE, 
        verbose_name="Категорія"
    )
    name = models.CharField(max_length=200, verbose_name="Назва товару")
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True, verbose_name="Опис")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна")
    image = models.ImageField(upload_to='products/%Y/%m/%d', blank=True, verbose_name="Зображення")
    stock = models.PositiveIntegerField(default=0, verbose_name="Залишок на складі")
    is_active = models.BooleanField(default=True, verbose_name="Активний")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товари"
        ordering = ['-created_at']

    def __str__(self):
        return self.name
    
    def get_average_rating(self):
            reviews = self.reviews.all()
            if reviews.exists():
                return round(sum(r.rating for r in reviews) / reviews.count(), 1)
            return 0


class Review(models.Model):
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='reviews',
        verbose_name="Товар"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='reviews',
        verbose_name="Автор"
    )
    rating = models.PositiveSmallIntegerField(
        verbose_name="Оцінка (1-5)",
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(verbose_name="Текст відгуку")
    image = models.ImageField(
        upload_to='review_photos/', 
        blank=True, 
        null=True, 
        verbose_name="Фото до відгуку"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Відгук"
        verbose_name_plural = "Відгуки"

    def __str__(self):
        return f"Відгук від {self.user.username} на {self.product.name} ({self.rating}★)"