from unittest.mock import Mock, patch

from rest_framework import status
from rest_framework.test import APITestCase


class ReviewApiTests(APITestCase):
	@patch("app.views.requests.get")
	def test_create_review_and_get_stats(self, mock_get):
		book_response = Mock()
		book_response.status_code = status.HTTP_200_OK
		book_response.raise_for_status.return_value = None
		mock_get.return_value = book_response

		payload = {
			"customer_id": 1,
			"book_id": 10,
			"rating": 4,
			"comment": "Great read",
		}
		create_response = self.client.post("/reviews/", payload, format="json")
		self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

		stats_response = self.client.get("/reviews/stats/10/")
		self.assertEqual(stats_response.status_code, status.HTTP_200_OK)
		self.assertEqual(stats_response.json()["total"], 1)
		self.assertEqual(stats_response.json()["avg_rating"], 4.0)
