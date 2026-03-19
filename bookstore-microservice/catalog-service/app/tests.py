from unittest.mock import Mock, patch

from rest_framework import status
from rest_framework.test import APITestCase


class CatalogApiTests(APITestCase):
	def test_create_and_list_categories(self):
		create_response = self.client.post(
			"/categories/",
			{"name": "Technology", "description": "Tech books"},
			format="json",
		)
		self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

		list_response = self.client.get("/categories/")
		self.assertEqual(list_response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(list_response.json()), 1)
		self.assertEqual(list_response.json()[0]["name"], "Technology")

	def test_create_tag(self):
		response = self.client.post("/tags/", {"name": "bestseller"}, format="json")
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)

	@patch("app.views.requests.get")
	def test_get_category_books_proxy(self, mock_get):
		self.client.post("/categories/", {"name": "Software"}, format="json")

		book_response = Mock()
		book_response.raise_for_status.return_value = None
		book_response.json.return_value = [{"id": 10, "catalog_id": 1, "title": "DDD"}]
		mock_get.return_value = book_response

		response = self.client.get("/categories/1/books/")
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.json()), 1)
		self.assertEqual(response.json()[0]["id"], 10)
