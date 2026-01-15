import logging
from typing import Any

import polars as pl
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class PolarsInternalResponse(JSONResponse):
    """
    Optimized JSON response for handling Polars DataFrames.
    Uses polars native serialization to avoid expensive pandas conversion.
    """

    def render(self, content: Any) -> bytes:
        if isinstance(content, pl.DataFrame):
            # Write to JSON string, then encode to bytes.
            # Efficient for medium payloads. large streaming endpoints should use StreamingResponse.
            try:
                # 'row' orientation is standard for frontend APIs (array of objects)
                return content.write_json(row_oriented=True).encode("utf-8")
            except Exception as e:
                logger.error(f"Failed to serialize DataFrame: {e}")
                # Fallback to empty list or strict error?
                # Let's panic safely
                return b"[]"

        return super().render(content)
