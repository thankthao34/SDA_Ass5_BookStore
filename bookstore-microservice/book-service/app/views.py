from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Book
from .serializers import BookSerializer


class BookListCreate(APIView):
	def get(self, request):
		books = Book.objects.all().order_by("id")
		author = request.query_params.get("author")
		catalog_id = request.query_params.get("catalog_id")
		if author:
			books = books.filter(author__icontains=author)
		if catalog_id:
			books = books.filter(catalog_id=catalog_id)
		serializer = BookSerializer(books, many=True)
		return Response(serializer.data)

	def post(self, request):
		serializer = BookSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response(serializer.data, status=status.HTTP_201_CREATED)


class BookDetail(APIView):
	def get_object(self, pk):
		try:
			return Book.objects.get(pk=pk)
		except Book.DoesNotExist:
			return None

	def get(self, request, pk):
		book = self.get_object(pk)
		if not book:
			return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
		return Response(BookSerializer(book).data)

	def put(self, request, pk):
		book = self.get_object(pk)
		if not book:
			return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
		serializer = BookSerializer(book, data=request.data)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response(serializer.data)

	def delete(self, request, pk):
		book = self.get_object(pk)
		if not book:
			return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
		book.delete()
		return Response(status=status.HTTP_204_NO_CONTENT)


class BookUpdateStock(APIView):
	def put(self, request, pk):
		try:
			book = Book.objects.get(pk=pk)
		except Book.DoesNotExist:
			return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

		decrease = int(request.data.get("decrease", 0) or 0)
		increase = int(request.data.get("increase", 0) or 0)
		new_stock = book.stock - decrease + increase
		if new_stock < 0:
			return Response(
				{"error": "Stock cannot be negative"},
				status=status.HTTP_400_BAD_REQUEST,
			)

		book.stock = new_stock
		book.save(update_fields=["stock", "updated_at"])
		return Response({"id": book.id, "stock": book.stock})
