from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from dentists.models import dentistProfile

class Command(BaseCommand):
    help = 'Create DentistProfiles for users without them'

    def handle(self, *args, **kwargs):

        User = get_user_model()
        users_without_profiles = User.objects.exclude(id__in=dentistProfile.objects.values_list('user_id', flat=True))


        for user in users_without_profiles:
            dentistProfile.objects.create(user=user)
            self.stdout.write(self.style.SUCCESS(f"Created DentistProfile for user: {user.username}"))