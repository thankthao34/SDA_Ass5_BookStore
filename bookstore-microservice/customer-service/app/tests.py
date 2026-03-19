from unittest.mock import patch

import requests
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Customer


class CustomerApiTests(APITestCase):
	def test_get_customers_returns_list(self):
		response = self.client.get("/customers/")
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.json(), [])

	@patch("app.views.requests.post")
	def test_create_customer_success_and_cart_created(self, mock_post):
		mock_post.return_value.status_code = 201
		payload = {"name": "Alice", "email": "alice@example.com"}

		response = self.client.post("/customers/", payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(Customer.objects.count(), 1)
		self.assertEqual(Customer.objects.first().email, "alice@example.com")
		mock_post.assert_called_once()

	@patch("app.views.requests.post", side_effect=requests.RequestException("down"))
	def test_create_customer_still_succeeds_when_cart_service_unavailable(self, _):
		payload = {"name": "Bob", "email": "bob@example.com"}

		response = self.client.post("/customers/", payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(Customer.objects.count(), 1)
