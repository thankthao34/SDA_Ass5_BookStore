import os

import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Customer
from .serializers import CustomerSerializer

CART_SERVICE_URL = os.getenv("CART_SERVICE_URL", "http://cart-service:8000")


class CustomerListCreate(APIView):
	def get(self, request):
		customers = Customer.objects.all().order_by("id")
		serializer = CustomerSerializer(customers, many=True)
		return Response(serializer.data)

	def post(self, request):
		serializer = CustomerSerializer(data=request.data)
		if serializer.is_valid():
			customer = serializer.save()
			try:
				requests.post(
					f"{CART_SERVICE_URL}/carts/",
					json={"customer_id": customer.id},
					timeout=5,
				)
			except requests.RequestException:
				pass
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerDetail(APIView):
	def get_object(self, pk):
		try:
			return Customer.objects.get(pk=pk)
		except Customer.DoesNotExist:
			return None

	def get(self, request, pk):
		customer = self.get_object(pk)
		if not customer:
			return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
		return Response(CustomerSerializer(customer).data)

	def put(self, request, pk):
		customer = self.get_object(pk)
		if not customer:
			return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
		serializer = CustomerSerializer(customer, data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	def delete(self, request, pk):
		customer = self.get_object(pk)
		if not customer:
			return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
		customer.delete()
		return Response(status=status.HTTP_204_NO_CONTENT)
