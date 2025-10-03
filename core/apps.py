from django.apps import AppConfig
from django.conf import settings
import os
class CoreConfig(AppConfig):
    name = "core"
    def ready(self):
        if not settings.PRELOAD_MODELS:
            return
        if os.environ.get("RUN_MAIN") == "true" or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            from .ml_service import get_service
            get_service().warm()
