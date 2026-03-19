from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
	ROLE_CHOICES = [
		("customer", "Customer"),
		("staff", "Staff"),
		("manager", "Manager"),
		("admin", "Admin"),
	]

	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="gateway_profile")
	role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="customer")
	customer_id = models.IntegerField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"UserProfile<{self.user.username}:{self.role}>"
