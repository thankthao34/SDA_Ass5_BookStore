from django.db import migrations
from django.contrib.auth.hashers import make_password


DEMO_USERS = [
	{"username": "admin", "password": "admin123", "role": "admin", "customer_id": None, "is_staff": True, "is_superuser": True},
	{"username": "staff", "password": "staff123", "role": "staff", "customer_id": None, "is_staff": True, "is_superuser": False},
	{"username": "manager", "password": "manager123", "role": "manager", "customer_id": None, "is_staff": True, "is_superuser": False},
	{"username": "customer", "password": "customer123", "role": "customer", "customer_id": 1, "is_staff": False, "is_superuser": False},
]


def create_demo_users(apps, schema_editor):
	user_model = apps.get_model("auth", "User")
	profile_model = apps.get_model("gateway", "UserProfile")

	for item in DEMO_USERS:
		user, created = user_model.objects.get_or_create(
			username=item["username"],
			defaults={
				"is_staff": item["is_staff"],
				"is_superuser": item["is_superuser"],
			},
		)
		if created:
			user.password = make_password(item["password"])
			user.save(update_fields=["password"])

		profile_model.objects.update_or_create(
			user=user,
			defaults={
				"role": item["role"],
				"customer_id": item["customer_id"],
			},
		)


def rollback_demo_users(apps, schema_editor):
	user_model = apps.get_model("auth", "User")
	profile_model = apps.get_model("gateway", "UserProfile")

	for username in ["admin", "staff", "manager", "customer"]:
		try:
			user = user_model.objects.get(username=username)
		except user_model.DoesNotExist:
			continue
		profile_model.objects.filter(user=user).delete()
		user.delete()


class Migration(migrations.Migration):

	dependencies = [
		("gateway", "0001_initial"),
	]

	operations = [
		migrations.RunPython(create_demo_users, rollback_demo_users),
	]
