from django.db import models


class Staff(models.Model):
	ROLE_CHOICES = [
		("admin", "Admin"),
		("staff", "Staff"),
		("librarian", "Librarian"),
	]

	name = models.CharField(max_length=255)
	email = models.EmailField(unique=True)
	role = models.CharField(max_length=50, choices=ROLE_CHOICES, default="staff")
	department = models.CharField(max_length=255, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.name} ({self.role})"
