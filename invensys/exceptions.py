from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import re


def _parse_integrity_error(exc: IntegrityError) -> tuple[str, str]:
    msg = str(exc)

    unique_match = re.search(r'Key \((.+?)\)=\((.+?)\) already exists', msg)
    if unique_match:
        field = unique_match.group(1)
        value = unique_match.group(2)
        return (f"A record with {field} '{value}' already exists.", 'unique')

    return (
        'A database integrity error occurred. The data you submitted conflicts with existing '
        'records.', 'integrity_error'
    )


def _parse_protected_error(exc: ProtectedError, context: dict) -> tuple[str, str]:
    """
    Auto-generate a detail message from the parent model name (via the view's
    queryset) and child model names (via exc.protected_objects).

    Example response body:
        { "code": "has_references",
          "detail": "Category cannot be deleted because it is still referenced by: product." }
    """

    parent_model = 'record'
    view = context.get('view')
    if view is not None:
        try:
            parent_model = view.get_queryset().model.__name__.lower()
        except Exception:
            pass

    references = sorted({obj.__class__.__name__.lower() for obj in exc.protected_objects})

    references_str = ', '.join(references) if references else 'other records'
    detail = (
        f"{parent_model.capitalize()} cannot be deleted because it is still "
        f"referenced by: {references_str}."
    )
    return detail, 'has_references'


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if (
        response is not None
        and response.status_code == status.HTTP_400_BAD_REQUEST
        and isinstance(response.data, dict)
    ):
        for field, errors in response.data.items():
            if hasattr(errors[0], 'code'):
                response.data = {
                    'detail': f"{errors[0]}" if isinstance(errors, list) else f"{errors}",
                    'code': errors[0].code
                }
                break
        return response

    if isinstance(exc, ProtectedError):
        detail, code = _parse_protected_error(exc, context)
        return Response({'detail': detail, 'code': code}, status=status.HTTP_409_CONFLICT)

    if isinstance(exc, IntegrityError):
        detail, code = _parse_integrity_error(exc)
        return Response({'detail': detail, 'code': code}, status=status.HTTP_409_CONFLICT)

    return None
