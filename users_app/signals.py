from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from auth_app.models import CustomUser
from users_app.models import UserProfile


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance: CustomUser, created: bool, **kwargs):
    """
    Automatically create a matching UserProfile for every new CustomUser.
    """
    if created and not hasattr(instance, "userprofile"):
        UserProfile.objects.create(user=instance, is_customer=False)