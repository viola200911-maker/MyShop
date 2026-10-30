from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.order_create, name='checkout'),
    path('success/<int:order_id>/', views.order_success, name='order_success'),
    path('my-orders/', views.order_list, name='order_list'),
    path('my-orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('my-orders/<int:order_id>/cancel-request/', views.order_cancel_request, name='order_cancel_request'),
    path('my-orders/<int:order_id>/reorder/', views.order_reorder, name='order_reorder'),
]