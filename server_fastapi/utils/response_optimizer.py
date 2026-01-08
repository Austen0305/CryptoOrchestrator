"""
Response Optimization Utilities
Helper functions for optimizing API responses
"""

import json
import logging
from typing import Any

from fastapi import Response
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)


class ResponseOptimizer:
    """Utility class for optimizing API responses"""

    @staticmethod
    def paginate_response(
        data: list[Any], page: int, page_size: int, total: int | None = None
    ) -> dict[str, Any]:
        """
        Create a paginated response with metadata.

        Args:
            data: List of items for current page
            page: Current page number (1-indexed)
            page_size: Items per page
            total: Total number of items (optional, will be len(data) if not provided)

        Returns:
            Dictionary with data, pagination metadata
        """
        if total is None:
            total = len(data)

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return {
            "data": data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            },
        }

    @staticmethod
    def filter_null_fields(data: dict[str, Any]) -> dict[str, Any]:
        """
        Remove null/None fields from response to reduce payload size.

        Args:
            data: Dictionary to filter

        Returns:
            Dictionary with null fields removed
        """
        if isinstance(data, dict):
            return {
                k: ResponseOptimizer.filter_null_fields(v)
                for k, v in data.items()
                if v is not None
            }
        elif isinstance(data, list):
            return [ResponseOptimizer.filter_null_fields(item) for item in data]
        return data

    @staticmethod
    def select_fields(
        data: dict[str, Any] | list[dict[str, Any]], fields: list[str]
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """
        Select only specified fields from response (sparse fieldsets).

        Args:
            data: Dictionary or list of dictionaries
            fields: List of field names to include

        Returns:
            Filtered data with only specified fields
        """
        if isinstance(data, list):
            return [{k: v for k, v in item.items() if k in fields} for item in data]
        elif isinstance(data, dict):
            return {k: v for k, v in data.items() if k in fields}
        return data

    @staticmethod
    def stream_large_response(
        data: list[Any], chunk_size: int = 1000
    ) -> StreamingResponse:
        """
        Stream large responses in chunks to reduce memory usage.

        Args:
            data: List of items to stream
            chunk_size: Number of items per chunk

        Returns:
            StreamingResponse
        """

        def generate_chunks():
            # Stream JSON array in chunks
            yield b"["
            for i, item in enumerate(data):
                if i > 0:
                    yield b","
                chunk = json.dumps(item, default=str).encode("utf-8")
                yield chunk
            yield b"]"

        return StreamingResponse(
            generate_chunks(),
            media_type="application/json",
            headers={
                "Content-Type": "application/json",
                "Transfer-Encoding": "chunked",
            },
        )

    @staticmethod
    def optimize_json_serialization(data: Any) -> bytes:
        """
        Optimize JSON serialization using orjson if available, fallback to json.

        Args:
            data: Data to serialize

        Returns:
            Serialized bytes
        """
        try:
            import orjson

            return orjson.dumps(data, option=orjson.OPT_SERIALIZE_NUMPY)
        except ImportError:
            # Fallback to standard json
            return json.dumps(data, default=str).encode("utf-8")

    @staticmethod
    def add_cache_headers(
        response: Response, max_age: int = 300, stale_while_revalidate: int = 60
    ) -> Response:
        """
        Add cache control headers to response.

        Args:
            response: FastAPI Response object
            max_age: Cache max age in seconds
            stale_while_revalidate: Stale-while-revalidate time in seconds

        Returns:
            Response with cache headers
        """
        cache_control = f"public, max-age={max_age}, stale-while-revalidate={stale_while_revalidate}"
        response.headers["Cache-Control"] = cache_control
        return response

    @staticmethod
    def add_compression_headers(response: Response) -> Response:
        """
        Add compression-related headers.

        Args:
            response: FastAPI Response object

        Returns:
            Response with compression headers
        """
        response.headers["Vary"] = "Accept-Encoding"
        return response
