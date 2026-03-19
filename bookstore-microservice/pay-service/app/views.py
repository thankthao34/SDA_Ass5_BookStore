from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment
from .serializers import PaymentSerializer


class PaymentListCreate(APIView):
	def get(self, request):
		return Response(PaymentSerializer(Payment.objects.all(), many=True).data)

	def post(self, request):
		serializer = PaymentSerializer(data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentByOrder(APIView):
	def get(self, request, order_id):
		try:
			payment = Payment.objects.get(order_id=order_id)
		except Payment.DoesNotExist:
			return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
		return Response(PaymentSerializer(payment).data)


class ConfirmPayment(APIView):
	def put(self, request, pk):
		try:
			payment = Payment.objects.get(pk=pk)
		except Payment.DoesNotExist:
			return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

		payment.status = "PAID"
		payment.paid_at = timezone.now()
		payment.transaction_ref = request.data.get("transaction_ref", "")
		payment.save()
		return Response(PaymentSerializer(payment).data)


class FailPayment(APIView):
	def put(self, request, pk):
		try:
			payment = Payment.objects.get(pk=pk)
		except Payment.DoesNotExist:
			return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

		payment.status = "FAILED"
		payment.save(update_fields=["status"])
		return Response(PaymentSerializer(payment).data)
