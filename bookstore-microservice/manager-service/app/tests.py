from rest_framework import status
from rest_framework.test import APITestCase


class ManagerApiTests(APITestCase):
	def test_create_and_list_managers(self):
		payload = {
			"name": "John Manager",
			"email": "john.manager@example.com",
			"department": "Operations",
			"level": "senior",
		}

		create_response = self.client.post("/managers/", payload, format="json")
		self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

		list_response = self.client.get("/managers/")
		self.assertEqual(list_response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(list_response.json()), 1)
		self.assertEqual(list_response.json()[0]["email"], "john.manager@example.com")
