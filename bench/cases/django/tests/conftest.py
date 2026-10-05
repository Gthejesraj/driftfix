import django
from django.conf import settings

settings.configure(
    ROOT_URLCONF="app", SECRET_KEY="test", ALLOWED_HOSTS=["testserver"],
    INSTALLED_APPS=[], MIDDLEWARE=[], USE_TZ=True,
)
django.setup()
