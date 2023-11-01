from django.apps import AppConfig
from rest_framework import HTTP_HEADER_ENCODING, exceptions
from rest_framework import authentication
from six import text_type

def get_authorization_header(request):
    
    """
    Return request's 'Authorization:' header, as a bytestring.
    Hide some test client ickyness where the header can be unicode.
    """
    from django.conf import settings
    
    auth = request.META.get('HTTP_'+settings.AUTH_TOKEN_NAME, b'')

    if isinstance(auth, text_type):
        # Work around django test client oddness
        auth = auth.encode(HTTP_HEADER_ENCODING)
    return auth

class AppConfig(AppConfig):
    name = 'rfl'
    verbose_name = "RFL"

    def ready(self):
        authentication.get_authorization_header = get_authorization_header
        #import api.signals
