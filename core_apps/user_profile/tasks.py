import base64
from uuid import UUID

import cloudinary.uploader
from celery import shared_task
from django.apps import apps
from django.core.files.storage import default_storage
from loguru import logger

@shared_task(name = 'upload image to cloudinary')
def upload_image_to_cloudinary(profile_id: UUID, images: dict) -> None:
    try:
        Profile = apps.get_model('user_profile', 'UserProfile')
        profile = Profile.objects.get(id=profile_id)

        for field_name, image_data in images.items():
            if image_data['type'] == 'base64':
                image_content = base64.b64decode(image_data['data'])
                response = cloudinary.uploader.upload(image_content)
            else:
                with open(image_data['path'], 'rb') as image_file:
                    response = cloudinary.uploader.upload(image_file)
                default_storage.delete(image_data['path'])
            
            setattr(profile, field_name, response['public_id'])
            setattr(profile, f'{field_name}_url', response['url'])
        
        profile.save()
        logger.info(f'Images for {profile.user.email}\'s uploaded successfully to Cloudinary')

    except Exception as e:
        logger.error(f'Failed to upload images for profile {profile_id}: {str(e)}')

        if image_data in images.values():
            if image_data['type'] == 'file' and default_storage.exists(image_data['path']):
                default_storage.delete(image_data['path'])
