from typing import Any, Type
from django.db.models import Model

from django.db.models.signals import post_save
from django.dispatch import receiver
from loguru import logger

from config.settings.base import AUTH_USER_MODEL
from core_apps.user_profile.models import UserProfile

@receiver(post_save, sender=AUTH_USER_MODEL)
def create_user_profile(sender: Type[Model], instance: Model, created: bool, **kwargs: Any) -> None:
    if created:
        logger.info('Creating user profile for new user')
        UserProfile.objects.create(user=instance)
    else:
        logger.info('Updating user profile for existing user')
        instance.profile.save()
