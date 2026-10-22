# Users/urls.py
from django.urls import path
from .views import register_view, UserLoginView, logout_view, home, profile_view, security_view
from django.contrib.auth import views as auth_views
from django.conf import settings
from .forms import CustomPasswordResetForm  # Імпортуємо форму

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('', home, name='home'),
    path('profile/', profile_view, name='profile'),
    path('profile/security/', security_view, name='security'),

    # Форма скидання пароля з підтримкою Google-акаунтів
    path('password-reset/', 
          auth_views.PasswordResetView.as_view(
          form_class=CustomPasswordResetForm,
          template_name='Users/password_reset_form.html',
          email_template_name='Users/password_reset_email.html',
          subject_template_name='Users/password_reset_subject.txt',
          from_email=settings.DEFAULT_FROM_EMAIL
          ), 
          name='password_reset'),
    
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='Users/password_reset_done.html'), 
         name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='Users/password_reset_confirm.html'), 
         name='password_reset_confirm'),
    
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='Users/password_reset_complete.html'), 
         name='password_reset_complete'),
]