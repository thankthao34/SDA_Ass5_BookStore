from django.urls import path

from .views import ConfirmPayment, FailPayment, PaymentByOrder, PaymentListCreate

urlpatterns = [
    path("payments/", PaymentListCreate.as_view(), name="payment-list"),
    path("payments/<int:order_id>/", PaymentByOrder.as_view(), name="payment-by-order"),
    path("payments/<int:pk>/confirm/", ConfirmPayment.as_view(), name="payment-confirm"),
    path("payments/<int:pk>/fail/", FailPayment.as_view(), name="payment-fail"),
]
