from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Shipment
from .serializers import ShipmentSerializer


class ShipmentListCreate(APIView):
	def get(self, request):
		return Response(ShipmentSerializer(Shipment.objects.all(), many=True).data)

	def post(self, request):
		serializer = ShipmentSerializer(data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShipmentByOrder(APIView):
	def get(self, request, order_id):
		try:
			shipment = Shipment.objects.get(order_id=order_id)
		except Shipment.DoesNotExist:
			return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
		return Response(ShipmentSerializer(shipment).data)


class UpdateShipmentStatus(APIView):
	def put(self, request, pk):
		try:
			shipment = Shipment.objects.get(pk=pk)
		except Shipment.DoesNotExist:
			return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

		status_value = request.data.get("status")
		valid_statuses = {choice[0] for choice in Shipment.STATUS_CHOICES}
		if status_value not in valid_statuses:
			return Response(
				{"error": "Invalid status"},
				status=status.HTTP_400_BAD_REQUEST,
			)

		shipment.status = status_value
		if status_value == "DELIVERED":
			shipment.delivered_at = timezone.now()
		shipment.save()
		return Response(ShipmentSerializer(shipment).data)
