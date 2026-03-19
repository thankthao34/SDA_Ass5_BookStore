from django.db import models


class Book(models.Model):
	title = models.CharField(max_length=255)
	author = models.CharField(max_length=255)
	price = models.DecimalField(max_digits=10, decimal_places=2)
	stock = models.IntegerField(default=0)
	description = models.TextField(blank=True)
	cover_url = models.URLField(blank=True)
	catalog_id = models.IntegerField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.title} ({self.author})"
