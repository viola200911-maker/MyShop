from django import forms
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from Shop.models import Product, Category
from Orders.models import Order

User = get_user_model()


class AdminUserEditForm(forms.ModelForm):
    """Форма редагування користувача для адміна"""
    is_active = forms.BooleanField(
        required=False, 
        label="Активний акаунт (зняти галочку для забанення)", 
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    is_staff = forms.BooleanField(
        required=False, 
        label="Права адміністратора (Staff)", 
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 
            'phone_number', 'date_of_birth', 'address', 'is_active', 'is_staff'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class AdminOrderEditForm(forms.ModelForm):
    """Форма редагування замовлення для адміна"""
    class Meta:
        model = Order
        fields = ['status', 'first_name', 'last_name', 'email', 'phone', 'address', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class ProductForm(forms.ModelForm):
    """Форма створення та редагування товарів"""
    slug = forms.CharField(
        required=False, 
        label="Slug (згенерується автоматично, якщо залишити порожнім)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'автоматично-з-назви'})
    )

    class Meta:
        model = Product
        fields = ['category', 'name', 'slug', 'price', 'stock', 'image', 'description', 'is_active']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.slug:
            instance.slug = slugify(instance.name)
        if commit:
            instance.save()
        return instance