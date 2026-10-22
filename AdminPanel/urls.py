from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.admin_dashboard, name='dashboard'),
    
    # Користувачі
    path('users/', views.user_list, name='user_list'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/toggle-ban/', views.toggle_user_ban, name='toggle_user_ban'),
    
    # Замовлення
    path('orders/', views.admin_order_list, name='admin_order_list'),
    path('orders/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    
    # Товари
    path('products/', views.admin_product_list, name='admin_product_list'),
    path('products/add/', views.product_add, name='product_add'),
    path('products/<int:product_id>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:product_id>/delete/', views.product_delete, name='product_delete'),
    path('review/delete/<int:review_id>/', views.delete_review, name='delete_review'),
]