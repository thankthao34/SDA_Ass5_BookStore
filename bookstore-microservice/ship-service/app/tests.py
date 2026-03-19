from rest_framework import status
from rest_framework.test import APITestCase


class ShipmentApiTests(APITestCase):
	def test_create_shipment_and_get_by_order(self):
		payload = {"order_id": 2001, "address": "Hanoi"}
		create_response = self.client.post("/shipments/", payload, format="json")
		self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
		self.assertTrue(create_response.json().get("tracking_code", "").startswith("TRK-"))

		get_response = self.client.get("/shipments/2001/")
		self.assertEqual(get_response.status_code, status.HTTP_200_OK)
		self.assertEqual(get_response.json()["order_id"], 2001)

	def test_update_shipment_status(self):
		create_response = self.client.post(
			"/shipments/",
			{"order_id": 2002, "address": "Da Nang"},
			format="json",
		)
		shipment_id = create_response.json()["id"]

		update_response = self.client.put(
			f"/shipments/{shipment_id}/status/",
			{"status": "DELIVERED"},
			format="json",
		)
		self.assertEqual(update_response.status_code, status.HTTP_200_OK)
		self.assertEqual(update_response.json()["status"], "DELIVERED")
