from django.urls import path

from .views import ShipmentByOrder, ShipmentListCreate, UpdateShipmentStatus

urlpatterns = [
    path("shipments/", ShipmentListCreate.as_view(), name="shipment-list"),
    path("shipments/<int:order_id>/", ShipmentByOrder.as_view(), name="shipment-by-order"),
    path("shipments/<int:pk>/status/", UpdateShipmentStatus.as_view(), name="shipment-status"),
]
