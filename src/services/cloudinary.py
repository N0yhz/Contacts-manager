"""
Cloudinary Service Module

This module provides functionality for uploading images to Cloudinary.

Dependencies:
    - os: For environment variable access
    - cloudinary: For Cloudinary API interactions
    - fastapi: For handling file uploads
    - dotenv: For loading environment variables

Functions:
    - upload_image: Upload an image file to Cloudinary

Configuration:
    - Loads Cloudinary configuration from environment variables

"""
import os
import cloudinary, cloudinary.uploader
from fastapi import UploadFile
from dotenv import load_dotenv

from src.database.database import logger

load_dotenv()

cloudinary.config(
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key = os.getenv("CLOUDINARY_API_KEY"),
    api_secret = os.getenv("CLOUDINARY_API_SECRET")
)

def upload_image(file: UploadFile) -> str:
   """
    Upload an image file to Cloudinary.

    :param file: The image file to upload
    :type file: UploadFile
    :return: The secure URL of the uploaded image
    :rtype: str
    :raises Exception: If there's an error uploading the image
    
    """
   try:
       result = cloudinary.uploader.upload(file.file)
       logger.info("Avatar uploaded successfully")
       return result["secure_url"]
   except Exception as e:
       logger.error(f"Error uploading avatar: {str(e)}")
       raise