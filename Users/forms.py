import re
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        required=True,
        label='Username',
        widget=forms.TextInput(attrs={'placeholder': 'Введіть username', 'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={'placeholder': 'example@gmail.com', 'class': 'form-control'})
    )
    first_name = forms.CharField(
        required=True,
        label="Ім'я",
        max_length=30,
        widget=forms.TextInput(attrs={'placeholder': "Введіть ім'я", 'class': 'form-control'})
    )
    last_name = forms.CharField(
        required=True,
        label='Прізвище',
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'Введіть прізвище', 'class': 'form-control'})
    )
    phone_number = forms.CharField(
        required=False,
        label='Номер телефону',
        widget=forms.TextInput(attrs={'placeholder': '+380971234567', 'class': 'form-control'})
    )
    date_of_birth = forms.DateField(
        required=False,
        label='Дата народження (для подарунків на ДН 🎂)',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    address = forms.CharField(
        required=False,
        label='Адреса доставки за замовчуванням',
        widget=forms.TextInput(attrs={'placeholder': 'Адреса доставки', 'class': 'form-control'})
    )
    avatar = forms.ImageField(
        required=False, 
        label='Аватар',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 'date_of_birth', 'address', 'avatar')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            return username
        if len(username) < 3:
            raise forms.ValidationError("Юзернейм має містити мінімум 3 символи")
        if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
            raise forms.ValidationError("Юзернейм може містити лише латинські літери, цифри, '_', '-' або '.'")
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Користувач з таким юзернеймом вже існує!")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            return email
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Користувач з таким email вже існує!")
        if email.lower().endswith('@test.com'):
            raise forms.ValidationError("Тестові email адреси заборонені!")
        return email

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not first_name:
            return first_name
        if not re.match(r'^[a-zA-Zа-яА-ЯіІїЇєЄ\'-]+$', first_name):
            raise forms.ValidationError("Ім'я має містити тільки букви")
        if len(first_name) < 2:
            raise forms.ValidationError("Ім'я має містити мінімум 2 символи")
        return first_name.title()

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not last_name:
            return last_name
        if not re.match(r'^[a-zA-Zа-яА-ЯіІїЇєЄ\'-]+$', last_name):
            raise forms.ValidationError("Прізвище має містити тільки букви")
        if len(last_name) < 2:
            raise forms.ValidationError("Прізвище має містити мінімум 2 символи")
        return last_name.title()

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if not phone:
            return phone
        cleaned_phone = re.sub(r'[\s\(\)\-]', '', phone)
        pattern = r'^(\+380\d{9}|0\d{9})$'
        if not re.match(pattern, cleaned_phone):
            raise forms.ValidationError("Введіть коректний номер телефону у форматі +380XXXXXXXXX або 0XXXXXXXXX")
        return cleaned_phone

    def clean(self):
        cleaned_data = super().clean()
        first_name = cleaned_data.get('first_name')
        username = cleaned_data.get('username')

        if first_name and username and first_name.lower() == username.lower():
            raise forms.ValidationError("Логін не може збігатися з ім'ям")
        return cleaned_data


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        label="Ім'я",
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label='Прізвище',
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    phone_number = forms.CharField(
        required=False,
        label='Номер телефону',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+380XXXXXXXXX'})
    )
    date_of_birth = forms.DateField(
        required=False,
        label='Дата народження',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    address = forms.CharField(
        required=False,
        label='Адреса доставки',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
    avatar = forms.ImageField(
        required=False,
        label='Аватар',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone_number', 'date_of_birth', 'address', 'avatar')

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if first_name:
            if not re.match(r'^[a-zA-Zа-яА-ЯіІїЇєЄ\'-]+$', first_name):
                raise forms.ValidationError("Ім'я має містити тільки літери")
            if len(first_name) < 2:
                raise forms.ValidationError("Ім'я має містити мінімум 2 символи")
            return first_name.title()
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if last_name:
            if not re.match(r'^[a-zA-Zа-яА-ЯіІїЇєЄ\'-]+$', last_name):
                raise forms.ValidationError("Прізвище має містити тільки літери")
            if len(last_name) < 2:
                raise forms.ValidationError("Прізвище має містити мінімум 2 символи")
            return last_name.title()
        return last_name

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if not phone:
            return phone
        cleaned_phone = re.sub(r'[\s\(\)\-]', '', phone)
        if not re.match(r'^(\+380\d{9}|0\d{9})$', cleaned_phone):
            raise forms.ValidationError("Формат телефону: +380XXXXXXXXX або 0XXXXXXXXX")
        return cleaned_phone


class UserSecurityForm(forms.Form):
    current_password = forms.CharField(
        label="Поточний пароль (для підтвердження дій)",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Введіть поточний пароль'})
    )
    username = forms.CharField(
        label='Логін (Username)',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    new_password = forms.CharField(
        required=False,
        label='Новий пароль (залиште порожнім, якщо не змінюєте)',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Мінімум 8 символів'})
    )
    confirm_password = forms.CharField(
        required=False,
        label='Підтвердження нового пароля',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        if not self.is_bound:
            self.fields['username'].initial = user.username
            self.fields['email'].initial = user.email

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise forms.ValidationError("Невірний поточний пароль!")
        return current_password

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            return username
        if len(username) < 3:
            raise forms.ValidationError("Юзернейм має містити мінімум 3 символи")
        if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
            raise forms.ValidationError("Юзернейм може містити лише латинські літери, цифри, '_', '-' або '.'")
        if User.objects.filter(username__iexact=username).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError("Користувач з таким юзернеймом вже існує!")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            return email
        if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError("Користувач з таким email вже існує!")
        if email.lower().endswith('@test.com'):
            raise forms.ValidationError("Тестові email адреси заборонені!")
        return email

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if self.user.first_name and username and self.user.first_name.lower() == username.lower():
            raise forms.ValidationError("Логін не може збігатися з ім'ям")

        if new_password or confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError("Нові паролі не збігаються!")
            if len(new_password) < 8:
                raise forms.ValidationError("Новий пароль має містити мінімум 8 символів!")
        return cleaned_data

    def save(self):
        self.user.username = self.cleaned_data['username']
        self.user.email = self.cleaned_data['email']
        new_password = self.cleaned_data.get('new_password')
        if new_password:
            self.user.set_password(new_password)
        self.user.save()
        return self.user


class CustomPasswordResetForm(PasswordResetForm):
    def get_users(self, email):
        """
        Повертає всіх активних користувачів з вказаним email,
        навіть якщо у них немає встановленого пароля (has_usable_password = False).
        """
        active_users = User.objects.filter(
            email__iexact=email,
            is_active=True
        )
        return active_users