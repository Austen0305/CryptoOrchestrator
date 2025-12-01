"""
API Response Utilities
Standardized response format helpers
"""
from typing import Any, Dict, Optional
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import status


def success_response(
    data: Any,
    status_code: int = status.HTTP_200_OK,
    message: Optional[str] = None,
    request: Optional[Request] = None
) -> Dict[str, Any]:
    """
    Create a standardized success response
    
    Args:
        data: Response data
        status_code: HTTP status code
        message: Optional success message
        request: FastAPI request object (for request_id)
    
    Returns:
        Standardized response dictionary
    """
    response = {
        "success": True,
        "data": data,
        "status_code": status_code
    }
    
    if message:
        response["message"] = message
    
    if request:
        request_id = getattr(request.state, "request_id", None)
        if request_id:
            response["request_id"] = request_id
    
    return response


def error_response(
    message: str,
    code: str = "ERROR",
    status_code: int = status.HTTP_400_BAD_REQUEST,
    details: Optional[Dict[str, Any]] = None,
    suggestion: Optional[str] = None,
    request: Optional[Request] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response
    
    Args:
        message: Error message
        code: Error code
        status_code: HTTP status code
        details: Additional error details
        suggestion: Helpful suggestion for user
        request: FastAPI request object (for request_id)
    
    Returns:
        Standardized error response dictionary
    """
    error = {
        "code": code,
        "message": message
    }
    
    if details:
        error["details"] = details
    
    if suggestion:
        error["suggestion"] = suggestion
    
    response = {
        "success": False,
        "error": error,
        "status_code": status_code
    }
    
    if request:
        request_id = getattr(request.state, "request_id", None)
        if request_id:
            response["request_id"] = request_id
    
    return response


def create_success_json_response(
    data: Any,
    status_code: int = status.HTTP_200_OK,
    message: Optional[str] = None,
    request: Optional[Request] = None
) -> JSONResponse:
    """Create a JSONResponse with standardized success format"""
    return JSONResponse(
        status_code=status_code,
        content=success_response(data, status_code, message, request)
    )


def create_error_json_response(
    message: str,
    code: str = "ERROR",
    status_code: int = status.HTTP_400_BAD_REQUEST,
    details: Optional[Dict[str, Any]] = None,
    suggestion: Optional[str] = None,
    request: Optional[Request] = None
) -> JSONResponse:
    """Create a JSONResponse with standardized error format"""
    return JSONResponse(
        status_code=status_code,
        content=error_response(message, code, status_code, details, suggestion, request)
    )

