from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


# FILE TO FIX THE BUG WITH AUTH WHEN PROJECT DEPLOYED
User = get_user_model()

class EmailBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None

        if user.check_password(password):
            return user
        return None