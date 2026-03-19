import uuid

from django.db import models


class Shipment(models.Model):
	STATUS_CHOICES = [
		("PENDING", "Pending"),
		("PROCESSING", "Processing"),
		("SHIPPED", "Shipped"),
		("IN_TRANSIT", "In Transit"),
		("DELIVERED", "Delivered"),
		("CANCELLED", "Cancelled"),
	]

	order_id = models.IntegerField()
	address = models.TextField()
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
	tracking_code = models.CharField(max_length=100, default="", blank=True)
	carrier = models.CharField(max_length=100, default="GHN", blank=True)
	estimated_at = models.DateTimeField(null=True, blank=True)
	delivered_at = models.DateTimeField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def save(self, *args, **kwargs):
		if not self.tracking_code:
			self.tracking_code = f"TRK-{uuid.uuid4().hex[:8].upper()}"
		super().save(*args, **kwargs)

	def __str__(self):
		return f"Shipment<{self.order_id}:{self.status}>"
