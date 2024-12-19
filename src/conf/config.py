import os
from dotenv import load_dotenv

load_dotenv()

# Determine if we're running in Docker
IN_DOCKER = os.environ.get("DOCKER_CONTAINER", False)

# Database configuration
if IN_DOCKER:
    DATABASE_URL = "postgresql://n0yhz:module11@db:5432/contacts_db"
else:
    DATABASE_URL = "postgresql://n0yhz:module11@localhost:5432/contacts_db"