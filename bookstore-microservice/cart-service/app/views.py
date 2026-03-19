import os

import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cart, CartItem
from .serializers import CartItemSerializer, CartSerializer

BOOK_SERVICE_URL = os.getenv("BOOK_SERVICE_URL", "http://book-service:8000")


class CartCreate(APIView):
	def post(self, request):
		serializer = CartSerializer(data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddCartItem(APIView):
	def post(self, request):
		book_id = request.data.get("book_id")
		cart_id = request.data.get("cart_id")
		quantity = int(request.data.get("quantity", 1) or 1)

		if not cart_id:
			return Response(
				{"error": "cart_id is required"},
				status=status.HTTP_400_BAD_REQUEST,
			)

		if quantity <= 0:
			return Response(
				{"error": "Quantity must be greater than 0"},
				status=status.HTTP_400_BAD_REQUEST,
			)

		if not Cart.objects.filter(pk=cart_id).exists():
			return Response({"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)

		try:
			response = requests.get(f"{BOOK_SERVICE_URL}/books/{book_id}/", timeout=5)
			if response.status_code == status.HTTP_404_NOT_FOUND:
				return Response({"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND)
			response.raise_for_status()
			book = response.json()
		except requests.RequestException:
			return Response(
				{"error": "book-service unavailable"},
				status=status.HTTP_503_SERVICE_UNAVAILABLE,
			)

		if book.get("stock", 0) < quantity:
			return Response(
				{"error": "Not enough stock"},
				status=status.HTTP_400_BAD_REQUEST,
			)

		data = {
			"cart": cart_id,
			"book_id": book_id,
			"quantity": quantity,
			"price_snapshot": book["price"],
		}
		serializer = CartItemSerializer(data=data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CartView(APIView):
	def get(self, request, customer_id):
		try:
			cart = Cart.objects.get(customer_id=customer_id)
		except Cart.DoesNotExist:
			return Response({"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)

		items = CartItem.objects.filter(cart=cart)
		return Response(
			{
				"cart_id": cart.id,
				"customer_id": cart.customer_id,
				"items": CartItemSerializer(items, many=True).data,
			}
		)


class UpdateCartItem(APIView):
	def put(self, request, pk):
		try:
			item = CartItem.objects.get(pk=pk)
		except CartItem.DoesNotExist:
			return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

		quantity = int(request.data.get("quantity", item.quantity) or item.quantity)
		if quantity <= 0:
			return Response(
				{"error": "Quantity must be greater than 0"},
				status=status.HTTP_400_BAD_REQUEST,
			)

		item.quantity = quantity
		item.save(update_fields=["quantity"])
		return Response(CartItemSerializer(item).data)

	def delete(self, request, pk):
		try:
			item = CartItem.objects.get(pk=pk)
		except CartItem.DoesNotExist:
			return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
		item.delete()
		return Response(status=status.HTTP_204_NO_CONTENT)


class ClearCart(APIView):
	def delete(self, request, cart_id):
		CartItem.objects.filter(cart_id=cart_id).delete()
		return Response(status=status.HTTP_204_NO_CONTENT)
