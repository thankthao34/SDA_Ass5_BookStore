from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Manager
from .serializers import ManagerSerializer


class ManagerListCreate(APIView):
	def get(self, request):
		serializer = ManagerSerializer(Manager.objects.all(), many=True)
		return Response(serializer.data)

	def post(self, request):
		serializer = ManagerSerializer(data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ManagerDetail(APIView):
	def get_object(self, pk):
		try:
			return Manager.objects.get(pk=pk)
		except Manager.DoesNotExist:
			return None

	def get(self, request, pk):
		obj = self.get_object(pk)
		if not obj:
			return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
		return Response(ManagerSerializer(obj).data)

	def put(self, request, pk):
		obj = self.get_object(pk)
		if not obj:
			return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
		serializer = ManagerSerializer(obj, data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	def delete(self, request, pk):
		obj = self.get_object(pk)
		if not obj:
			return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
		obj.delete()
		return Response(status=status.HTTP_204_NO_CONTENT)
