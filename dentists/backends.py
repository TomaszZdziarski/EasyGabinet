from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, email=None, password=None, **kwargs):
        logger.warning(f"EmailBackend called with username={username}, email={email}")
        try:
            user = User.objects.get(email=email or username)
            logger.warning(f"User found: {user.email}, checking password...")
            if user.check_password(password):
                logger.warning("Password correct!")
                return user
            logger.warning("Password incorrect!")
            return None
        except User.DoesNotExist:
            logger.warning("User not found!")
            return None