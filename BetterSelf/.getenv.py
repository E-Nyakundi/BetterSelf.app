from os import getenv

ALLOWED_HOSTS = [
    getenv('APP_HOST', http://127.0.0.1:8000/,)
]

SECRET_KEY = getenv('seret')
DEBUG = getenv("IS_DEVELOPMENT", True)