from django.urls import path

from .views import CategoryBooks, CategoryDetail, CategoryListCreate, TagListCreate

urlpatterns = [
    path("categories/", CategoryListCreate.as_view(), name="category-list"),
    path("categories/<int:pk>/", CategoryDetail.as_view(), name="category-detail"),
    path("categories/<int:pk>/books/", CategoryBooks.as_view(), name="category-books"),
    path("tags/", TagListCreate.as_view(), name="tag-list"),
]
