from django.db import connection
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    from django.conf import settings

    try:
        connection.ensure_connection()
        db_status = True
    except Exception:
        db_status = False


    return Response({
        'backend_status': 'ok',
        'version': settings.APP_VERSION,
        'env': settings.APP_STATUS,
        'debug': settings.DEBUG,
        'database': db_status,
    })