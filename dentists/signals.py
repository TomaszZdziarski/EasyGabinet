from django.db.models.signals import post_save,post_delete
from django.conf import settings
from .models import dentistProfile
from django.contrib.auth import get_user_model


# WHENEVER THE NEW USER (in our case: tomuleniek, like an admin person) IS CREATED WE WANT TO CONNECT IT
# AUTOMATICALLY TO PROFILE (a new dev profile)

User = get_user_model()

def createProfile(sender, instance, created, **kwargs):

    if created and not instance.is_superuser:

        if instance.user_type == 'dentist':

            profile = dentistProfile.objects.create(
                user = instance,  # UWAGA na przecinek tutaj,może spowodować 'tuple object doesn not have e-mail field etc'
                user_type='dentist'
                                          )

            # this copies same fields from User to Profile
# sender = Model that sends this, instance = instance of the Model that triggers this, created = True/False
# if user was created before or not


# if you go to admin panel and add NEW USER than NEW PROFILE WILL APPEAR  cos they are connected
# line: post_save.connect(createProfile, sender=User)
# everytime username is created in the new Profile,the same username from User will be given

# FUNCTION THAT SECURES THAT IF WE CHANGE IN PROFILES NAME OR USERNAME OR EMAIL THEN ALL CHANGES HAPPEN ALSO IN USERS(SO LIKE STEP ABOVE)

def updateUser(sender,instance,created,**kwargs):

    user = instance.user

    if created == False:
        user.save()



# WHAT IF PROFILE IS DELETED BUT NOT USER? WE NEED POST DELETE SIGNAL

def deleteUser(sender,instance,**kwargs):   # fixed bug:  User matching query does not exist.


    try:
        user = instance.user
        user.delete()
    except User.DoesNotExist:
        print('User deletion was called from CASCADE')

# THOSE ARE OUR CONNECTORS

post_save.connect(createProfile, sender=User)  # WE CHANGED SENDER TO USER,SENDER IS AN OBJECT WHICH IS BEING CREATED
post_save.connect(updateUser, sender=dentistProfile) # SENDER IS AN OBJECT WHICH IS BEING UPDATED
post_delete.connect(deleteUser,sender=dentistProfile) # ...DELETED


# NOTE: IF YOU DELETE NOW A USER, A CONNECTED PROFILE WILL ALSO BE REMOVED THX TO RELATIONSHIP:
# class Profile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
