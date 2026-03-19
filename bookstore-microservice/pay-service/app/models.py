from django.db import models


class Payment(models.Model):
	METHOD_CHOICES = [
		("cod", "Cash on Delivery"),
		("bank", "Bank Transfer"),
		("card", "Card"),
	]
	STATUS_CHOICES = [
		("PENDING", "Pending"),
		("PAID", "Paid"),
		("FAILED", "Failed"),
	]

	order_id = models.IntegerField()
	method = models.CharField(max_length=20, choices=METHOD_CHOICES, default="cod")
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
	amount = models.DecimalField(max_digits=12, decimal_places=2)
	transaction_ref = models.CharField(max_length=100, blank=True)
	paid_at = models.DateTimeField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Payment<{self.order_id}:{self.status}>"
