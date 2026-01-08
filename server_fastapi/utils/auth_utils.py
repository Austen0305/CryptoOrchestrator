"""
Authentication utility functions.
Centralizes common authentication-related operations.
"""


def get_user_id_from_payload(payload: dict) -> str | None:
    """
    Extract user ID from JWT payload, supporting both 'id' and 'sub' keys.

    Args:
        payload: JWT payload dictionary

    Returns:
        User ID string, or None if not found

    Example:
        >>> payload = {"id": "123", "email": "user@example.com"}
        >>> get_user_id_from_payload(payload)
        '123'

        >>> payload = {"sub": "456", "email": "user@example.com"}
        >>> get_user_id_from_payload(payload)
        '456'
    """
    return payload.get("id") or payload.get("sub")
