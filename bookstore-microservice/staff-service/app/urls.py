from django.urls import path

from .views import StaffDetail, StaffListCreate

urlpatterns = [
    path("staffs/", StaffListCreate.as_view(), name="staff-list"),
    path("staffs/<int:pk>/", StaffDetail.as_view(), name="staff-detail"),
]
