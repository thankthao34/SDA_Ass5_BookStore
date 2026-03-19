from django.urls import path

from .views import AddCartItem, CartCreate, CartView, ClearCart, UpdateCartItem

urlpatterns = [
    path("carts/", CartCreate.as_view(), name="cart-create"),
    path("carts/<int:customer_id>/", CartView.as_view(), name="cart-view"),
    path("cart-items/", AddCartItem.as_view(), name="cart-items"),
    path("cart-items/<int:pk>/", UpdateCartItem.as_view(), name="cart-item-detail"),
    path("carts/<int:cart_id>/items/", ClearCart.as_view(), name="clear-cart"),
]
