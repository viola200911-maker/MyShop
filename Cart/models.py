from django.db import models
from django.conf import settings
from Shop.models import Product

class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Кошик користувача {self.user.username}"

    def get_total_items(self):
        """Підрахунок загальної кількості товарів у БД-кошику"""
        return sum(item.quantity for item in self.items.all())

    def get_total_price(self):
        """Загальна сума товарів у БД-кошику"""
        return sum(item.get_total_price() for item in self.items.all())

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзини"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} шт. - {self.product.name}"
    
    def get_total_price(self):
        return self.product.price * self.quantity

    class Meta:
        verbose_name = "Елемент корзини"
        verbose_name_plural = "Елементи корзини"