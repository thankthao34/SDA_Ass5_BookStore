import os

import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Tag
from .serializers import CategorySerializer, TagSerializer

BOOK_SERVICE_URL = os.getenv("BOOK_SERVICE_URL", "http://book-service:8000")


class CategoryListCreate(APIView):
	def get(self, request):
		serializer = CategorySerializer(Category.objects.all(), many=True)
		return Response(serializer.data)

	def post(self, request):
		serializer = CategorySerializer(data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryDetail(APIView):
	def get_object(self, pk):
		try:
			return Category.objects.get(pk=pk)
		except Category.DoesNotExist:
			return None

	def get(self, request, pk):
		obj = self.get_object(pk)
		if not obj:
			return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
		return Response(CategorySerializer(obj).data)

	def put(self, request, pk):
		obj = self.get_object(pk)
		if not obj:
			return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
		serializer = CategorySerializer(obj, data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryBooks(APIView):
	def get(self, request, pk):
		if not Category.objects.filter(pk=pk).exists():
			return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
		try:
			response = requests.get(f"{BOOK_SERVICE_URL}/books/?catalog_id={pk}", timeout=5)
			response.raise_for_status()
			return Response(response.json())
		except requests.RequestException:
			return Response(
				{"error": "book-service unavailable"},
				status=status.HTTP_503_SERVICE_UNAVAILABLE,
			)


class TagListCreate(APIView):
	def get(self, request):
		return Response(TagSerializer(Tag.objects.all(), many=True).data)

	def post(self, request):
		serializer = TagSerializer(data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
