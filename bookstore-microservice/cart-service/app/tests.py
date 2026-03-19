from unittest.mock import Mock, patch

from rest_framework import status
from rest_framework.test import APITestCase

from .models import Cart, CartItem


class CartApiTests(APITestCase):
	def test_create_cart(self):
		response = self.client.post("/carts/", {"customer_id": 1}, format="json")
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(Cart.objects.count(), 1)

	@patch("app.views.requests.get")
	def test_add_cart_item_success(self, mock_get):
		cart = Cart.objects.create(customer_id=1)

		mock_response = Mock()
		mock_response.status_code = 200
		mock_response.raise_for_status.return_value = None
		mock_response.json.return_value = {"id": 99, "title": "DDD", "price": "29.99", "stock": 10}
		mock_get.return_value = mock_response

		payload = {"cart_id": cart.id, "book_id": 99, "quantity": 2}
		response = self.client.post("/cart-items/", payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(CartItem.objects.count(), 1)

	@patch("app.views.requests.get")
	def test_add_cart_item_with_unknown_book(self, mock_get):
		cart = Cart.objects.create(customer_id=2)

		mock_response = Mock()
		mock_response.status_code = 404
		mock_get.return_value = mock_response

		payload = {"cart_id": cart.id, "book_id": 11, "quantity": 1}
		response = self.client.post("/cart-items/", payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
		self.assertEqual(CartItem.objects.count(), 0)

	def test_view_cart_by_customer(self):
		cart = Cart.objects.create(customer_id=3)
		CartItem.objects.create(cart=cart, book_id=1, quantity=4, price_snapshot="10.00")

		response = self.client.get("/carts/3/")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.json()["customer_id"], 3)
		self.assertEqual(len(response.json()["items"]), 1)
		self.assertEqual(response.json()["items"][0]["quantity"], 4)
