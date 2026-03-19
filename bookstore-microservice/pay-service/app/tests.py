from rest_framework import status
from rest_framework.test import APITestCase


class PaymentApiTests(APITestCase):
	def test_create_and_get_payment_by_order(self):
		payload = {"order_id": 1001, "method": "cod", "amount": "89.90"}
		create_response = self.client.post("/payments/", payload, format="json")
		self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

		get_response = self.client.get("/payments/1001/")
		self.assertEqual(get_response.status_code, status.HTTP_200_OK)
		self.assertEqual(get_response.json()["order_id"], 1001)

	def test_confirm_payment(self):
		create_response = self.client.post(
			"/payments/",
			{"order_id": 1002, "method": "card", "amount": "120.00"},
			format="json",
		)
		payment_id = create_response.json()["id"]

		confirm_response = self.client.put(
			f"/payments/{payment_id}/confirm/",
			{"transaction_ref": "TXN-123"},
			format="json",
		)
		self.assertEqual(confirm_response.status_code, status.HTTP_200_OK)
		self.assertEqual(confirm_response.json()["status"], "PAID")
