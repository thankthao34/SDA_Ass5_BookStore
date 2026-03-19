from django.db import models


class Order(models.Model):
	STATUS_CHOICES = [
		("PENDING", "Pending"),
		("CONFIRMED", "Confirmed"),
		("CANCELLED", "Cancelled"),
	]

	customer_id = models.IntegerField()
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
	total_price = models.DecimalField(max_digits=12, decimal_places=2)
	pay_method = models.CharField(max_length=50, default="cod")
	ship_address = models.TextField()
	payment_id = models.IntegerField(null=True, blank=True)
	shipment_id = models.IntegerField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Order<{self.id}:{self.customer_id}:{self.status}>"


class OrderItem(models.Model):
	order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
	book_id = models.IntegerField()
	quantity = models.IntegerField()
	price = models.DecimalField(max_digits=10, decimal_places=2)
	title_snapshot = models.CharField(max_length=255)

	def __str__(self):
		return f"OrderItem<{self.order_id}:{self.book_id}>"
