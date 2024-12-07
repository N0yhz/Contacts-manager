import os
from src.database.database import logger
import cloudinary, cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key = os.getenv("CLOUDINARY_API_KEY"),
    api_secret = os.getenv("CLOUDINARY_API_SECRET")
)

def upload_avatar(file) -> str:
   try:
       result = cloudinary.uploader.upload(file)
       logger.info("Avatar uploaded successfully")
       return result["secure_url"]
   except Exception as e:
       logger.error(f"Error uploading avatar: {str(e)}")
       raise