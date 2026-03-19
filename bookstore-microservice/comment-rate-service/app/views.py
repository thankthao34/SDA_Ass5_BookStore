import os

import requests
from django.db.models import Avg, Count
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Review
from .serializers import ReviewSerializer

BOOK_SERVICE_URL = os.getenv("BOOK_SERVICE_URL", "http://book-service:8000")


class ReviewListCreate(APIView):
	def get(self, request):
		reviews = Review.objects.all().order_by("-created_at")
		return Response(ReviewSerializer(reviews, many=True).data)

	def post(self, request):
		book_id = request.data.get("book_id")
		try:
			response = requests.get(f"{BOOK_SERVICE_URL}/books/{book_id}/", timeout=5)
			if response.status_code == status.HTTP_404_NOT_FOUND:
				return Response({"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND)
			response.raise_for_status()
		except requests.RequestException:
			return Response(
				{"error": "book-service unavailable"},
				status=status.HTTP_503_SERVICE_UNAVAILABLE,
			)

		serializer = ReviewSerializer(data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReviewByBook(APIView):
	def get(self, request, book_id):
		reviews = Review.objects.filter(book_id=book_id).order_by("-created_at")
		return Response(ReviewSerializer(reviews, many=True).data)


class ReviewByCustomer(APIView):
	def get(self, request, customer_id):
		reviews = Review.objects.filter(customer_id=customer_id).order_by("-created_at")
		return Response(ReviewSerializer(reviews, many=True).data)


class ReviewDetail(APIView):
	def put(self, request, pk):
		try:
			review = Review.objects.get(pk=pk)
		except Review.DoesNotExist:
			return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

		serializer = ReviewSerializer(review, data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	def delete(self, request, pk):
		try:
			review = Review.objects.get(pk=pk)
		except Review.DoesNotExist:
			return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
		review.delete()
		return Response(status=status.HTTP_204_NO_CONTENT)


class ReviewStats(APIView):
	def get(self, request, book_id):
		reviews = Review.objects.filter(book_id=book_id)
		stats = reviews.aggregate(avg_rating=Avg("rating"), total=Count("id"))
		return Response(
			{
				"book_id": book_id,
				"avg_rating": round(stats["avg_rating"] or 0, 1),
				"total": stats["total"],
			}
		)


class ReviewStatsAll(APIView):
	def get(self, request):
		stats = (
			Review.objects.values("book_id")
			.annotate(avg_rating=Avg("rating"), total=Count("id"))
			.order_by("book_id")
		)
		return Response(
			[
				{
					"book_id": row["book_id"],
					"avg_rating": round(float(row["avg_rating"] or 0), 2),
					"total": row["total"],
				}
				for row in stats
			]
		)
