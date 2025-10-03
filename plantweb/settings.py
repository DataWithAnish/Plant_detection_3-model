from pathlib import Path
import os
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = "dev-only"
DEBUG = True
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "core",
]
MIDDLEWARE = []
ROOT_URLCONF = "plantweb.urls"
WSGI_APPLICATION = "plantweb.wsgi.application"
ASGI_APPLICATION = "plantweb.asgi.application"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": []},
}]
STATIC_URL = "/static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
INFERENCE_CODE_DIR = BASE_DIR / "inference_code"
PRELOAD_MODELS = True
