from rest_framework.views import exception_handler

from apps.core.responses.builders import api_error


def drf_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response
    response.data = api_error("Request failed", response.data)
    return response
