from django.db import models
from django.conf import settings
from Shop.models import Product

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Очікує обробки'),
        ('processing', 'В обробці'),
        ('shipped', 'Відправлено'),
        ('delivered', 'Доставлено'),
        ('cancelled', 'Скасовано'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    first_name = models.CharField(max_length=50, verbose_name="Ім'я")
    last_name = models.CharField(max_length=50, verbose_name="Прізвище")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    address = models.TextField(verbose_name="Адреса доставки")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(verbose_name="Примітка", blank=True, null=True)
    is_default = models.BooleanField(default=False, verbose_name="Основна адреса")
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Замовлення"
        verbose_name_plural = "Замовлення"

    @property
    def total_items_quantity(self):
        return sum(item.quantity for item in self.items.all())

    def __str__(self):
        return f"Замовлення №{self.id}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна на момент покупки")
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"