from pydantic import BaseModel, Field
from typing import Optional


class ErrorDetail(BaseModel):
    """
    Standardized error response model for consistent API error reporting.
    """
    error: str = Field(..., description="Error message describing what went wrong")
    detail: Optional[str] = Field(None, description="Optional additional error details")


def create_error_response(message: str, detail: Optional[str] = None) -> dict:
    """
    Helper function to create a standardized error response dictionary.
    
    Args:
        message: The main error message
        detail: Optional additional error details
        
    Returns:
        A dictionary with the error information formatted according to ErrorDetail model
    """
    error_model = ErrorDetail(error=message, detail=detail)
    return error_model.model_dump() 