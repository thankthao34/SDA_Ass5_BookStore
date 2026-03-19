from unittest.mock import Mock, patch

from rest_framework import status
from rest_framework.test import APITestCase

from .models import Order, OrderItem


class OrderApiTests(APITestCase):
	def test_get_orders_returns_list(self):
		response = self.client.get("/orders/")
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.json(), [])

	@patch("app.views.requests.delete")
	@patch("app.views.requests.put")
	@patch("app.views.requests.post")
	@patch("app.views.requests.get")
	def test_create_order_success(self, mock_get, mock_post, mock_put, mock_delete):
		book_response = Mock()
		book_response.status_code = status.HTTP_200_OK
		book_response.json.return_value = {
			"id": 1,
			"title": "Domain-Driven Design",
			"price": "50.00",
			"stock": 10,
		}
		mock_get.return_value = book_response

		pay_response = Mock()
		pay_response.status_code = status.HTTP_201_CREATED
		pay_response.json.return_value = {"id": 101}

		ship_response = Mock()
		ship_response.status_code = status.HTTP_201_CREATED
		ship_response.json.return_value = {"id": 202}

		mock_post.side_effect = [pay_response, ship_response]
		mock_put.return_value = Mock(status_code=status.HTTP_200_OK)
		mock_delete.return_value = Mock(status_code=status.HTTP_204_NO_CONTENT)

		payload = {
			"customer_id": 1,
			"items": [{"book_id": 1, "quantity": 2}],
			"pay_method": "cod",
			"ship_address": "Hanoi",
			"cart_id": 1,
		}

		response = self.client.post("/orders/", payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(Order.objects.count(), 1)
		self.assertEqual(OrderItem.objects.count(), 1)
		self.assertEqual(response.json()["status"], "CONFIRMED")

	def test_create_order_with_empty_items_fails(self):
		payload = {"customer_id": 1, "items": []}
		response = self.client.post("/orders/", payload, format="json")
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
