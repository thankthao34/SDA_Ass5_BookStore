import json
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import UserProfile


class GatewayTests(TestCase):
	def setUp(self):
		user_model = get_user_model()
		self.user = user_model.objects.create_user(username="gateway_test", password="test123")
		UserProfile.objects.create(user=self.user, role="customer", customer_id=1)

		self.manager = user_model.objects.create_user(username="manager_test", password="test123")
		UserProfile.objects.create(user=self.manager, role="manager")

		self.staff = user_model.objects.create_user(username="staff_test", password="test123")
		UserProfile.objects.create(user=self.staff, role="staff")

	@patch("gateway.views.requests.get")
	def test_books_page_renders(self, mock_get):
		self.client.force_login(self.user)

		books_response = Mock()
		books_response.raise_for_status.return_value = None
		books_response.json.return_value = []
		mock_get.return_value = books_response

		response = self.client.get("/books/")
		self.assertEqual(response.status_code, 200)

	@patch("gateway.views.requests.post")
	def test_create_order_proxy(self, mock_post):
		self.client.force_login(self.user)

		order_response = Mock()
		order_response.status_code = 201
		order_response.content = b'{"id": 1, "status": "CONFIRMED"}'
		order_response.json.return_value = {"id": 1, "status": "CONFIRMED"}
		mock_post.return_value = order_response

		payload = {
			"customer_id": 1,
			"items": [{"book_id": 1, "quantity": 1}],
			"ship_address": "HCM",
		}
		response = self.client.post(
			"/orders/",
			data=json.dumps(payload),
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.json()["status"], "CONFIRMED")

	@patch("gateway.views.requests.get")
	def test_manage_orders_forbidden_for_customer(self, mock_get):
		self.client.force_login(self.user)

		response = self.client.get("/ops/orders/")

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, "/")
		mock_get.assert_not_called()

	@patch("gateway.views.requests.get")
	def test_manage_shipments_allowed_for_staff(self, mock_get):
		self.client.force_login(self.staff)

		ship_response = Mock()
		ship_response.raise_for_status.return_value = None
		ship_response.json.return_value = []
		mock_get.return_value = ship_response

		response = self.client.get("/ops/shipments/")

		self.assertEqual(response.status_code, 200)
		mock_get.assert_called_once()

	@patch("gateway.views.requests.get")
	def test_non_customer_cart_post_is_blocked(self, mock_get):
		self.client.force_login(self.manager)

		cart_response = Mock()
		cart_response.status_code = 200
		cart_response.raise_for_status.return_value = None
		cart_response.json.return_value = {"cart_id": 99, "items": []}
		mock_get.side_effect = [cart_response, cart_response]

		response = self.client.post(
			"/cart/1/",
			data={"action": "checkout", "pay_method": "cod", "ship_address": "A"},
		)

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, "/cart/1/")

	@patch("gateway.views.requests.post")
	@patch("gateway.views.requests.get")
	def test_customer_add_to_cart_from_books(self, mock_get, mock_post):
		self.client.force_login(self.user)

		cart_response = Mock()
		cart_response.raise_for_status.return_value = None
		cart_response.json.return_value = {"cart_id": 5, "items": []}

		books_response = Mock()
		books_response.raise_for_status.return_value = None
		books_response.json.return_value = [{"id": 1, "title": "Book", "author": "A", "price": "10.00", "stock": 3}]

		mock_get.side_effect = [cart_response, books_response]

		add_response = Mock()
		add_response.status_code = 201
		mock_post.return_value = add_response

		response = self.client.post(
			"/books/",
			data={"action": "add_to_cart", "book_id": "1", "quantity": "2"},
		)

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, "/cart/1/")
		mock_post.assert_called_once()
