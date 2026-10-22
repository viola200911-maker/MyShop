# Shop/urls.py
from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('search/', views.search_prod, name='search_prod'),
    path('', views.product_list_view, name='product_list'),
    path('category/<slug:category_slug>/', views.product_list_view, name='product_list_by_category'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
]