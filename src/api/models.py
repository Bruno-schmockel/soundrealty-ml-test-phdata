"""Pydantic models for API request/response validation."""

from typing import Optional
from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """Request model for full home prediction."""
    bedrooms: int = Field(..., description="Number of bedrooms")
    bathrooms: float = Field(..., description="Number of bathrooms")
    sqft_living: int = Field(..., description="Living area square footage")
    sqft_lot: int = Field(..., description="Lot area square footage")
    floors: float = Field(..., description="Number of floors")
    sqft_above: int = Field(..., description="Square footage above ground")
    sqft_basement: int = Field(..., description="Square footage of basement")
    zipcode: str = Field(..., description="5-digit zipcode")

    class Config:
        json_schema_extra = {
            "example": {
                "bedrooms": 3,
                "bathrooms": 2.0,
                "sqft_living": 2000,
                "sqft_lot": 5000,
                "floors": 2.0,
                "sqft_above": 1500,
                "sqft_basement": 500,
                "zipcode": "98001"
            }
        }


class PredictionMinimalRequest(BaseModel):
    """Request model with only required features for prediction."""
    bedrooms: int = Field(..., description="Number of bedrooms")
    bathrooms: float = Field(..., description="Number of bathrooms")
    sqft_living: int = Field(..., description="Living area square footage")
    sqft_lot: int = Field(..., description="Lot area square footage")
    floors: float = Field(..., description="Number of floors")
    sqft_above: int = Field(..., description="Square footage above ground")
    sqft_basement: int = Field(..., description="Square footage of basement")
    zipcode: str = Field(..., description="5-digit zipcode")

    class Config:
        json_schema_extra = {
            "example": {
                "bedrooms": 3,
                "bathrooms": 2.0,
                "sqft_living": 2000,
                "sqft_lot": 5000,
                "floors": 2.0,
                "sqft_above": 1500,
                "sqft_basement": 500,
                "zipcode": "98001"
            }
        }


class PredictionResponse(BaseModel):
    """Response model for prediction."""
    prediction: float = Field(..., description="Predicted home price in USD")
    model_version: str = Field(..., description="Version of the model used")
    confidence: Optional[float] = Field(None, description="Confidence score (0-1)")

    class Config:
        json_schema_extra = {
            "example": {
                "prediction": 425000.50,
                "model_version": "1.0.0",
                "confidence": 0.85
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    model_loaded: bool = Field(..., description="Whether the model is loaded")
    demographics_loaded: bool = Field(..., description="Whether demographics data is loaded")
