from django.db import models


class Manager(models.Model):
	LEVEL_CHOICES = [
		("junior", "Junior"),
		("senior", "Senior"),
		("director", "Director"),
	]

	name = models.CharField(max_length=255)
	email = models.EmailField(unique=True)
	department = models.CharField(max_length=255)
	level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default="junior")
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.name} ({self.level})"
