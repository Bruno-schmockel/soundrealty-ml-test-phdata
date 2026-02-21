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
    waterfront: int = Field(..., description="Waterfront property (0 or 1)")
    view: int = Field(..., description="View quality (0-4)")
    condition: int = Field(..., description="Condition rating (1-5)")
    grade: int = Field(..., description="Building grade (1-13)")
    sqft_above: int = Field(..., description="Square footage above ground")
    sqft_basement: int = Field(..., description="Square footage of basement")
    yr_built: int = Field(..., description="Year built")
    yr_renovated: int = Field(..., description="Year renovated (0 if never)")
    zipcode: str = Field(..., description="5-digit zipcode")
    lat: float = Field(..., description="Latitude")
    long: float = Field(..., description="Longitude")
    sqft_living15: int = Field(..., description="Living area of 15 nearest neighbors")
    sqft_lot15: int = Field(..., description="Lot area of 15 nearest neighbors")

    class Config:
        json_schema_extra = {
            "example": {
                "bedrooms": 3,
                "bathrooms": 2.0,
                "sqft_living": 2000,
                "sqft_lot": 5000,
                "floors": 2.0,
                "waterfront": 0,
                "view": 0,
                "condition": 3,
                "grade": 7,
                "sqft_above": 1500,
                "sqft_basement": 500,
                "yr_built": 2000,
                "yr_renovated": 0,
                "zipcode": "98001",
                "lat": 47.5,
                "long": -122.3,
                "sqft_living15": 1800,
                "sqft_lot15": 5000
            }
        }


class PredictionMinimalRequest(BaseModel):
    """Request model with minimal required features for prediction."""
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
