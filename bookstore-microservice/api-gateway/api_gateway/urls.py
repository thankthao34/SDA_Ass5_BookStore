"""
URL configuration for api_gateway project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from gateway.views import (
    book_detail,
    book_list,
    catalog_overview,
    create_order,
    customer_list,
    login_view,
    manager_directory,
    manage_orders,
    manage_shipments,
    logout_view,
    order_history,
    payments_overview,
    profile_home,
    recommendations,
    review_hub,
    staff_directory,
    view_cart,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', profile_home, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('customers/', customer_list, name='customers'),
    path('books/', book_list, name='books'),
    path('books/<int:book_id>/', book_detail, name='book-detail'),
    path('catalog/', catalog_overview, name='catalog'),
    path('staffs/', staff_directory, name='staffs'),
    path('managers/', manager_directory, name='managers'),
    path('cart/<int:customer_id>/', view_cart, name='cart'),
    path('orders/', create_order, name='order-create'),
    path('orders/<int:customer_id>/', order_history, name='orders'),
    path('ops/orders/', manage_orders, name='manage-orders'),
    path('ops/payments/', payments_overview, name='payments'),
    path('ops/shipments/', manage_shipments, name='manage-shipments'),
    path('reviews/', review_hub, name='reviews'),
    path('recommendations/<int:customer_id>/', recommendations, name='recommendations'),
]
