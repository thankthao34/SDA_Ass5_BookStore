from django.urls import path

from .views import BookDetail, BookListCreate, BookUpdateStock

urlpatterns = [
    path("books/", BookListCreate.as_view(), name="books"),
    path("books/<int:pk>/", BookDetail.as_view(), name="book-detail"),
    path("books/<int:pk>/stock/", BookUpdateStock.as_view(), name="book-stock"),
]
