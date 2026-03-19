from .models import UserProfile


def gateway_user_profile(request):
	if not request.user.is_authenticated:
		return {"auth_profile": None}

	profile, _ = UserProfile.objects.get_or_create(
		user=request.user,
		defaults={"role": "customer"},
	)
	return {"auth_profile": profile}
