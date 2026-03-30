import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agent.settings")
django.setup()