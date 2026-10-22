from django import forms
from .models import Order

class OrderCreateForm(forms.ModelForm):
    PAYMENT_CHOICES = [
        ('cash', 'Готівкою при отриманні'),
        ('card', 'Оплата карткою онлайн'),
        ('bank', 'Банківський переказ'),
    ]

    payment_method = forms.ChoiceField(
        label='Спосіб оплати',
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Order
        fields = [
            'first_name', 'last_name', 'phone', 'email', 'address', 'notes', 'is_default'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ім\'я'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Прізвище'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+380...'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'example@gmail.com'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Місто, вулиця, будинок, квартира'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Додаткова інформація для кур\'єра (необов\'язково)'
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['notes', 'is_default']:
                field.required = True