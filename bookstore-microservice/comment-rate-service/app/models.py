from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Review(models.Model):
	customer_id = models.IntegerField()
	book_id = models.IntegerField()
	rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
	comment = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["customer_id", "book_id"], name="unique_customer_book_review")
		]

	def __str__(self):
		return f"Review<{self.customer_id}:{self.book_id}>"
