from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, email=None, password=None, **kwargs):
        login_email = (email or username or "").strip()
        logger.warning(f"EmailBackend: trying login_email='{login_email}'")

        if not login_email:
            logger.warning("EmailBackend: no email provided, aborting")
            return None

        try:
            user = User.objects.get(email__iexact=login_email)
            logger.warning(f"EmailBackend: found user '{user.email}'")
            if user.check_password(password):
                logger.warning("EmailBackend: password correct, returning user")
                return user
            logger.warning("EmailBackend: wrong password")
            return None
        except User.DoesNotExist:
            logger.warning(f"EmailBackend: no user found with email='{login_email}'")
            return None