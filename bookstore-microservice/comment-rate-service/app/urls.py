from django.urls import path

from .views import ReviewByBook, ReviewByCustomer, ReviewDetail, ReviewListCreate, ReviewStats, ReviewStatsAll

urlpatterns = [
    path("reviews/", ReviewListCreate.as_view(), name="review-list"),
    path("reviews/book/<int:book_id>/", ReviewByBook.as_view(), name="review-by-book"),
    path("reviews/customer/<int:customer_id>/", ReviewByCustomer.as_view(), name="review-by-customer"),
    path("reviews/<int:pk>/", ReviewDetail.as_view(), name="review-detail"),
    path("reviews/stats/", ReviewStatsAll.as_view(), name="review-stats-all"),
    path("reviews/stats/<int:book_id>/", ReviewStats.as_view(), name="review-stats"),
]
