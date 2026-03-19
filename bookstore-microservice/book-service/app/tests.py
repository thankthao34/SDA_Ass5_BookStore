from rest_framework import status
from rest_framework.test import APITestCase


class BookApiTests(APITestCase):
	def test_create_and_list_books(self):
		payload = {
			"title": "Clean Architecture",
			"author": "Robert C. Martin",
			"price": "35.00",
			"stock": 50,
		}

		create_response = self.client.post("/books/", payload, format="json")
		self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

		list_response = self.client.get("/books/")
		self.assertEqual(list_response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(list_response.json()), 1)
		self.assertEqual(list_response.json()[0]["title"], "Clean Architecture")
