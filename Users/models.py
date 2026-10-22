from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    phone_number = models.CharField(
        max_length=15, 
        blank=True, 
        null=True, 
        verbose_name="Номер телефону"
    )
    date_of_birth = models.DateField(
        blank=True, 
        null=True, 
        verbose_name="Дата народження"
    )
    address = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Адреса доставки за замовчуванням"
    )
    avatar = models.ImageField(
        upload_to='avatars/', 
        blank=True, 
        null=True, 
        verbose_name="Аватар"
    )

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "Користувач"
        verbose_name_plural = "Користувачі"