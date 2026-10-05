import datetime

from django.conf.urls import url
from django.http import JsonResponse
from django.utils.encoding import force_text
from django.utils.timezone import utc
from django.utils.translation import ugettext as _


def status(request):
    return JsonResponse({
        "message": force_text(_("ok")),
        "since": datetime.datetime(2020, 1, 1, tzinfo=utc).isoformat(),
        "ajax": request.is_ajax(),
    })


urlpatterns = [url(r"^status/$", status)]
