import os
from decimal import Decimal

import requests
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order, OrderItem
from .serializers import OrderSerializer

BOOK_SERVICE_URL = os.getenv("BOOK_SERVICE_URL", "http://book-service:8000")
PAY_SERVICE_URL = os.getenv("PAY_SERVICE_URL", "http://pay-service:8000")
SHIP_SERVICE_URL = os.getenv("SHIP_SERVICE_URL", "http://ship-service:8000")
CART_SERVICE_URL = os.getenv("CART_SERVICE_URL", "http://cart-service:8000")


class OrdersView(APIView):
	def get(self, request):
		orders = Order.objects.all().order_by("-created_at")
		return Response(OrderSerializer(orders, many=True).data)

	def post(self, request):
		if "customer_id" not in request.data or "items" not in request.data:
			return Response(
				{"error": "customer_id and items are required"},
				status=status.HTTP_400_BAD_REQUEST,
			)

		customer_id = request.data["customer_id"]
		items = request.data["items"]
		pay_method = request.data.get("pay_method", "cod")
		ship_address = request.data.get("ship_address", "")
		cart_id = request.data.get("cart_id")

		if not isinstance(items, list) or not items:
			return Response(
				{"error": "items must be a non-empty list"},
				status=status.HTTP_400_BAD_REQUEST,
			)

		validated_items = []
		total = Decimal("0")

		for item in items:
			book_id = item.get("book_id")
			quantity = int(item.get("quantity", 0) or 0)
			if quantity <= 0:
				return Response(
					{"error": "quantity must be greater than 0"},
					status=status.HTTP_400_BAD_REQUEST,
				)

			try:
				book_response = requests.get(f"{BOOK_SERVICE_URL}/books/{book_id}/", timeout=5)
				if book_response.status_code != status.HTTP_200_OK:
					return Response(
						{"error": f"Book {book_id} not found"},
						status=status.HTTP_404_NOT_FOUND,
					)
				book = book_response.json()
			except requests.RequestException:
				return Response(
					{"error": "book-service unavailable"},
					status=status.HTTP_503_SERVICE_UNAVAILABLE,
				)

			if book.get("stock", 0) < quantity:
				return Response(
					{"error": f"Not enough stock for \"{book.get('title', 'unknown')}\""},
					status=status.HTTP_400_BAD_REQUEST,
				)

			price = Decimal(str(book["price"]))
			validated_items.append(
				{
					"book_id": book_id,
					"quantity": quantity,
					"price": price,
					"title": book.get("title", ""),
				}
			)
			total += price * quantity

		with transaction.atomic():
			order = Order.objects.create(
				customer_id=customer_id,
				status="PENDING",
				total_price=total,
				pay_method=pay_method,
				ship_address=ship_address,
			)

			for item in validated_items:
				OrderItem.objects.create(
					order=order,
					book_id=item["book_id"],
					quantity=item["quantity"],
					price=item["price"],
					title_snapshot=item["title"],
				)

		try:
			pay_response = requests.post(
				f"{PAY_SERVICE_URL}/payments/",
				json={"order_id": order.id, "amount": str(total), "method": pay_method},
				timeout=5,
			)
			if pay_response.status_code < 400:
				order.payment_id = pay_response.json().get("id")
		except requests.RequestException:
			pass

		try:
			ship_response = requests.post(
				f"{SHIP_SERVICE_URL}/shipments/",
				json={"order_id": order.id, "address": ship_address},
				timeout=5,
			)
			if ship_response.status_code < 400:
				order.shipment_id = ship_response.json().get("id")
		except requests.RequestException:
			pass

		order.status = "CONFIRMED"
		order.save()

		for item in validated_items:
			try:
				requests.put(
					f"{BOOK_SERVICE_URL}/books/{item['book_id']}/stock/",
					json={"decrease": item["quantity"]},
					timeout=5,
				)
			except requests.RequestException:
				pass

		if cart_id:
			try:
				requests.delete(f"{CART_SERVICE_URL}/carts/{cart_id}/items/", timeout=5)
			except requests.RequestException:
				pass

		return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrdersByCustomer(APIView):
	def get(self, request, customer_id):
		orders = Order.objects.filter(customer_id=customer_id).order_by("-created_at")
		return Response(OrderSerializer(orders, many=True).data)


class OrderDetail(APIView):
	def get(self, request, pk):
		try:
			order = Order.objects.get(pk=pk)
		except Order.DoesNotExist:
			return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
		return Response(OrderSerializer(order).data)


class UpdateOrderStatus(APIView):
	def put(self, request, pk):
		try:
			order = Order.objects.get(pk=pk)
		except Order.DoesNotExist:
			return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

		new_status = request.data.get("status")
		valid_statuses = {choice[0] for choice in Order.STATUS_CHOICES}
		if new_status not in valid_statuses:
			return Response(
				{"error": "Invalid status"},
				status=status.HTTP_400_BAD_REQUEST,
			)

		order.status = new_status
		order.save(update_fields=["status"])
		return Response(OrderSerializer(order).data)


