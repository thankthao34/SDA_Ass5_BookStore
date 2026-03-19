from django.db import models


class Category(models.Model):
	name = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	parent_id = models.IntegerField(null=True, blank=True)

	def __str__(self):
		return self.name


class Tag(models.Model):
	name = models.CharField(max_length=100, unique=True)

	def __str__(self):
		return self.name
