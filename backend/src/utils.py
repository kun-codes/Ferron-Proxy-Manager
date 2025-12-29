"""
Utility functions to generate FastAPI response schemas from exception classes.
This allows error responses to be automatically derived from exception definitions.
"""
from typing import Any, Dict, Type

from fastapi import HTTPException


def generate_error_response(
    exception_class: Type[HTTPException],
    *args: Any,
    **kwargs: Any
) -> Dict[int, Dict[str, Any]]:
    """
    will generate a fastapi response schema from an exception class. Useful for OpenAPI documentation

    Args:
        exception_class: The exception class to generate response from
        *args: Positional arguments to pass to the exception constructor
        **kwargs: Keyword arguments to pass to the exception constructor

    Returns:
        A dict with the status code as key and response schema as value

    Example:
        @router.get(
            "/global",
            responses=generate_error_response(ConfigNotFound, "global configuration")
        )
    """
    exc_instance = exception_class(*args, **kwargs)

    status_code = exc_instance.status_code
    detail = exc_instance.detail

    if isinstance(detail, dict) and "message" in detail:
        description = detail["message"]
    else:
        description = str(detail)

    return {
        status_code: {
            "description": description,
            "content": {
                "application/json": {
                    "example": {
                        "detail": detail
                    }
                }
            }
        }
    }


def merge_responses(*response_dicts: Dict[int, Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """
    Merge multiple response dictionaries into one.

    Args:
        *response_dicts: Variable number of response dictionaries to merge

    Returns:
        A single merged dictionary

    Example:
        @router.patch(
            "/global",
            responses=merge_responses(
                generate_error_response(ConfigNotFound, "global configuration"),
                generate_error_response(GlobalConfigAlreadyExists)
            )
        )
    """
    merged = {}
    for resp_dict in response_dicts:
        merged.update(resp_dict)
    return merged
