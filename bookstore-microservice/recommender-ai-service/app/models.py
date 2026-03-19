from django.db import models


class Recommendation(models.Model):
	customer_id = models.IntegerField(unique=True)
	book_ids_json = models.TextField(blank=True)
	model_version = models.CharField(max_length=30, default="hybrid-v1")
	updated_at = models.DateTimeField(auto_now=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Recommendation<{self.customer_id}>"
