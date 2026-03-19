from rest_framework import status
from rest_framework.test import APITestCase


class StaffApiTests(APITestCase):
	def test_create_and_list_staffs(self):
		payload = {
			"name": "Alice",
			"email": "alice.staff@example.com",
			"role": "staff",
			"department": "Sales",
		}

		create_response = self.client.post("/staffs/", payload, format="json")
		self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

		list_response = self.client.get("/staffs/")
		self.assertEqual(list_response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(list_response.json()), 1)
		self.assertEqual(list_response.json()[0]["email"], "alice.staff@example.com")
