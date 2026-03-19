from unittest.mock import Mock, patch

from rest_framework import status
from rest_framework.test import APITestCase


class RecommenderApiTests(APITestCase):
	@patch("app.views.requests.get")
	def test_train_endpoint(self, mock_get):
		def fake_get(url, timeout=5):
			response = Mock()
			response.raise_for_status.return_value = None
			response.status_code = status.HTTP_200_OK

			if url.endswith("/orders/"):
				response.json.return_value = [
					{"customer_id": 1, "items": [{"book_id": 1, "quantity": 1}]},
					{"customer_id": 2, "items": [{"book_id": 2, "quantity": 1}]},
				]
			elif url.endswith("/books/"):
				response.json.return_value = [
					{"id": 1, "catalog_id": 10, "title": "Book A", "stock": 10},
					{"id": 2, "catalog_id": 10, "title": "Book B", "stock": 10},
					{"id": 3, "catalog_id": 11, "title": "Book C", "stock": 10},
				]
			elif "/reviews/stats/" in url:
				response.json.return_value = {"avg_rating": 4.0, "total": 3}
			else:
				raise AssertionError(f"Unexpected URL called: {url}")

			return response

		mock_get.side_effect = fake_get

		response = self.client.post("/recommendations/train/", {}, format="json")
		self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
		self.assertEqual(response.json()["customers_processed"], 2)

	@patch("app.views.requests.get")
	def test_get_recommendations_by_customer(self, mock_get):
		def fake_get(url, timeout=5):
			response = Mock()
			response.raise_for_status.return_value = None
			response.status_code = status.HTTP_200_OK

			if url.endswith("/orders/"):
				response.json.return_value = [
					{"customer_id": 99, "items": [{"book_id": 1, "quantity": 1}]},
					{"customer_id": 100, "items": [{"book_id": 2, "quantity": 3}]},
				]
			elif url.endswith("/books/"):
				response.json.return_value = [
					{"id": 1, "catalog_id": 10, "title": "Bought", "stock": 5},
					{"id": 2, "catalog_id": 10, "title": "Recommended", "stock": 6},
					{"id": 3, "catalog_id": 11, "title": "Other", "stock": 8},
				]
			elif url.endswith("/reviews/stats/2/"):
				response.json.return_value = {"avg_rating": 4.8, "total": 10}
			elif url.endswith("/reviews/stats/3/"):
				response.json.return_value = {"avg_rating": 3.5, "total": 5}
			else:
				raise AssertionError(f"Unexpected URL called: {url}")

			return response

		mock_get.side_effect = fake_get

		response = self.client.get("/recommendations/99/")
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.json()["customer_id"], 99)
		self.assertEqual(response.json()["total"], 2)
		self.assertEqual(response.json()["recommendations"][0]["id"], 2)
