from django.urls import path

from .views import GetRecommendationsByCustomer, TrainRecommendations

urlpatterns = [
    path("recommendations/<int:customer_id>/", GetRecommendationsByCustomer.as_view(), name="recommendations"),
    path("recommendations/train/", TrainRecommendations.as_view(), name="recommendations-train"),
]
