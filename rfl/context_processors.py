from django.conf import settings

def export_vars(request):
    data = {}
    data['DEPLOYED_ENVIRONMENT'] = settings.DEPLOYED_ENVIRONMENT
    return data
