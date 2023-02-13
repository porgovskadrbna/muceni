import os

import dotenv

dotenv.load_dotenv()

TORTOISE_ORM = {
    "connections": {"default": os.getenv("DB_URL")},
    "apps": {"models": {"models": ["aerich.models", "models.filenames"]}},
}
