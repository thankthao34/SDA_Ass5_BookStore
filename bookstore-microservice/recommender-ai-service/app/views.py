import os
import json
from collections import defaultdict

import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Recommendation

ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8000")
BOOK_SERVICE_URL = os.getenv("BOOK_SERVICE_URL", "http://book-service:8000")
COMMENT_RATE_SERVICE_URL = os.getenv("COMMENT_RATE_SERVICE_URL", "http://comment-rate-service:8000")
MODEL_VERSION = "hybrid-v1"


def _safe_get_json(url, timeout=5):
	last_exc = None
	for _ in range(3):
		try:
			response = requests.get(url, timeout=timeout)
			response.raise_for_status()
			return response.json(), None
		except requests.RequestException as exc:
			last_exc = exc
	return None, last_exc


def _build_book_index(all_books):
	return {book.get("id"): book for book in all_books if book.get("id") is not None}


def _compute_purchase_frequency(all_orders):
	freq = defaultdict(int)
	for order in all_orders:
		for item in order.get("items", []):
			book_id = item.get("book_id")
			if book_id is None:
				continue
			qty = int(item.get("quantity", 1) or 1)
			freq[book_id] += max(qty, 1)
	return freq


def _build_rating_map():
	rating_map = {}
	stats_rows, stats_error = _safe_get_json(f"{COMMENT_RATE_SERVICE_URL}/reviews/stats/", timeout=6)
	if stats_error or not isinstance(stats_rows, list):
		return rating_map

	for row in stats_rows:
		book_id = row.get("book_id")
		if book_id is None:
			continue
		try:
			rating_map[book_id] = float(row.get("avg_rating") or 0)
		except (TypeError, ValueError):
			rating_map[book_id] = 0.0

	return rating_map


def _generate_recommendations(customer_id, customer_orders, all_orders, all_books, rating_map):
	book_index = _build_book_index(all_books)
	purchase_frequency = _compute_purchase_frequency(all_orders)

	bought_ids = set()
	catalog_affinity = defaultdict(int)

	for order in customer_orders:
		for item in order.get("items", []):
			book_id = item.get("book_id")
			if book_id is None:
				continue
			qty = int(item.get("quantity", 1) or 1)
			bought_ids.add(book_id)
			catalog_id = book_index.get(book_id, {}).get("catalog_id")
			if catalog_id is not None:
				catalog_affinity[catalog_id] += max(qty, 1)

	candidates = []
	for book in all_books:
		book_id = book.get("id")
		if book_id is None or book_id in bought_ids:
			continue
		if int(book.get("stock", 0) or 0) <= 0:
			continue

		catalog_id = book.get("catalog_id")
		affinity = float(catalog_affinity.get(catalog_id, 0))
		popularity = float(purchase_frequency.get(book_id, 0))
		avg_rating = float(rating_map.get(book_id, 0.0))

		score = (affinity * 3.0) + (popularity * 0.35) + (avg_rating * 1.4)

		candidate = {
			**book,
			"score": round(score, 3),
			"avg_rating": round(avg_rating, 2),
			"popularity": int(popularity),
			"catalog_affinity": int(affinity),
		}
		candidates.append(candidate)

	if not candidates:
		return []

	candidates.sort(key=lambda x: (x.get("score", 0), x.get("avg_rating", 0), x.get("popularity", 0)), reverse=True)
	return candidates[:10]


def _upsert_cache(customer_id, recommendations):
	Recommendation.objects.update_or_create(
		customer_id=customer_id,
		defaults={
			"book_ids_json": json.dumps([book.get("id") for book in recommendations]),
			"model_version": MODEL_VERSION,
		},
	)


class GetRecommendations(APIView):
	def get(self, request):
		return Response({"error": "customer_id is required"}, status=status.HTTP_400_BAD_REQUEST)


class GetRecommendationsByCustomer(APIView):
	def get(self, request, customer_id):
		all_orders, order_error = _safe_get_json(f"{ORDER_SERVICE_URL}/orders/", timeout=6)
		if order_error:
			return Response(
				{"error": "order-service unavailable"},
				status=status.HTTP_503_SERVICE_UNAVAILABLE,
			)

		all_books, book_error = _safe_get_json(f"{BOOK_SERVICE_URL}/books/", timeout=6)
		if book_error:
			return Response(
				{"error": "book-service unavailable"},
				status=status.HTTP_503_SERVICE_UNAVAILABLE,
			)

		customer_orders = [order for order in all_orders if order.get("customer_id") == customer_id]
		rating_map = _build_rating_map()
		recommended = _generate_recommendations(
			customer_id=customer_id,
			customer_orders=customer_orders,
			all_orders=all_orders,
			all_books=all_books,
			rating_map=rating_map,
		)

		_upsert_cache(customer_id, recommended)

		return Response(
			{
				"customer_id": customer_id,
				"recommendations": recommended,
				"total": len(recommended),
				"model_version": MODEL_VERSION,
				"trained_from_orders": len(customer_orders),
			}
		)


class TrainRecommendations(APIView):
	def post(self, request):
		all_orders, order_error = _safe_get_json(f"{ORDER_SERVICE_URL}/orders/", timeout=8)
		if order_error:
			return Response({"error": "order-service unavailable"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

		all_books, book_error = _safe_get_json(f"{BOOK_SERVICE_URL}/books/", timeout=8)
		if book_error:
			return Response({"error": "book-service unavailable"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

		customer_ids = sorted({order.get("customer_id") for order in all_orders if order.get("customer_id") is not None})
		rating_map = _build_rating_map()

		for customer_id in customer_ids:
			customer_orders = [order for order in all_orders if order.get("customer_id") == customer_id]
			recommended = _generate_recommendations(
				customer_id=customer_id,
				customer_orders=customer_orders,
				all_orders=all_orders,
				all_books=all_books,
				rating_map=rating_map,
			)
			_upsert_cache(customer_id, recommended)

		return Response(
			{
				"message": "Training completed",
				"model_version": MODEL_VERSION,
				"customers_processed": len(customer_ids),
			},
			status=status.HTTP_202_ACCEPTED,
		)
