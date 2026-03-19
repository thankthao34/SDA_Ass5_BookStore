from django.db import models


class Cart(models.Model):
	customer_id = models.IntegerField(unique=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Cart<{self.customer_id}>"


class CartItem(models.Model):
	cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
	book_id = models.IntegerField()
	quantity = models.IntegerField(default=1)
	price_snapshot = models.DecimalField(max_digits=10, decimal_places=2)
	added_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"CartItem<{self.cart_id}:{self.book_id}>"
