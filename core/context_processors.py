import os

def site_name(request):
    return {
        'sitename': os.getenv("SITE_NAME"),
        'site_admin_individual_name': os.getenv("SITE_ADMIN_INDIVIDUAL_NAME")
    }