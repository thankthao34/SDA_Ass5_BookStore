from django.urls import path

from .views import CustomerDetail, CustomerListCreate

urlpatterns = [
    path("customers/", CustomerListCreate.as_view(), name="customers"),
    path("customers/<int:pk>/", CustomerDetail.as_view(), name="customer-detail"),
]
