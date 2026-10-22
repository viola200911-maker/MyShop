from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'date_of_birth', 'is_staff']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Додаткова інформація', {
            'fields': ('phone_number', 'date_of_birth', 'address', 'avatar')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Додаткова інформація', {
            'fields': ('phone_number', 'date_of_birth', 'address', 'avatar')
        }),
    )