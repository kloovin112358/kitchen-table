import zoneinfo
from django.utils import timezone
import os

class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tzname = request.session.get("django_timezone")
        if tzname:
            print("NOT DEFAULT!!!")
            timezone.activate(zoneinfo.ZoneInfo(tzname))
            print(timezone.get_current_timezone_name())
        else:
            print("DEFAULT!!!!")
            timezone.activate(zoneinfo.ZoneInfo(os.getenv("DEFAULT_DISPLAY_TIMEZONE")))
            print(timezone.get_current_timezone_name())
        return self.get_response(request)