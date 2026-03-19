from django.urls import path

from .views import OrderDetail, OrdersByCustomer, OrdersView, UpdateOrderStatus

urlpatterns = [
    path("orders/", OrdersView.as_view(), name="order-list-create"),
    path("orders/customer/<int:customer_id>/", OrdersByCustomer.as_view(), name="orders-by-customer"),
    path("orders/<int:pk>/", OrderDetail.as_view(), name="order-detail"),
    path("orders/<int:pk>/status/", UpdateOrderStatus.as_view(), name="order-status"),
]
