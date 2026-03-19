from django.urls import path

from .views import ManagerDetail, ManagerListCreate

urlpatterns = [
    path("managers/", ManagerListCreate.as_view(), name="manager-list"),
    path("managers/<int:pk>/", ManagerDetail.as_view(), name="manager-detail"),
]
