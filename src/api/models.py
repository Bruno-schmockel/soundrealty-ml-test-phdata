"""Pydantic models for API request/response validation."""


from pydantic import BaseModel, ConfigDict, Field


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
    
    model_config = ConfigDict(
        json_schema_extra={
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
    )


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
    
    model_config = ConfigDict(
        json_schema_extra={
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
    )


class PredictionResponse(BaseModel):
    """Response model for prediction."""
    prediction: float = Field(..., description="Predicted home price in USD")
    model_name: str = Field(..., description="Name of the model used for prediction")
    api_instance_id: str = Field(..., description="API instance identifier (endpoint and model)")
    call_id: str = Field(..., description="Unique identifier for this prediction call")
    explanation: dict = Field(default=None, description="Explanation of the prediction with feature importance")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "prediction": 425000.50,
                "model_name": "added_features",
                "api_instance_id": "predict-added_features",
                "call_id": "550e8400-e29b-41d4-a716-446655440000",
                "explanation": {
                    "prediction_confidence": 0.85,
                    "key_drivers": ["hous_val_amt", "medn_incm_per_prsn_amt"],
                    "top_features": [
                        {
                            "feature": "hous_val_amt",
                            "importance": 0.15,
                            "z_score": 0.4
                        }
                    ]
                }
            }
        }
    )


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    model_loaded: bool = Field(..., description="Whether the model is loaded")
    demographics_loaded: bool = Field(..., description="Whether demographics data is loaded")


class FeatureImportanceItem(BaseModel):
    """Feature importance item."""
    feature: str = Field(..., description="Feature name")
    importance: float = Field(..., description="Importance score")
    std: float = Field(..., description="Standard deviation of importance")


class FeatureAnalysisItem(BaseModel):
    """Feature analysis for prediction explanation."""
    feature: str = Field(..., description="Feature name")
    value: float = Field(..., description="Feature value in prediction")
    mean: float = Field(..., description="Mean value across dataset")
    std: float = Field(..., description="Standard deviation")
    z_score: float = Field(..., description="Z-score (standard deviations from mean)")
    importance: float = Field(..., description="Feature importance score")
    analysis: str = Field(..., description="Natural language analysis of the feature")


class PredictionExplanationResponse(BaseModel):
    """Response model for prediction explanation."""
    model_name: str = Field(..., description="Name of the model used")
    prediction: float = Field(..., description="Predicted home price")
    feature_analysis: list[FeatureAnalysisItem] = Field(..., description="Analysis of top features")
    prediction_confidence: float = Field(..., description="Confidence score (0-1)")
    key_drivers: list[str] = Field(..., description="Names of top 5 most influential features")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "model_name": "basic",
                "prediction": 425000.50,
                "feature_analysis": [
                    {
                        "feature": "hous_val_amt",
                        "value": 200000,
                        "mean": 180000,
                        "std": 50000,
                        "z_score": 0.4,
                        "importance": 0.15,
                        "analysis": "slightly unusual, above average (z=0.40) - HIGH IMPACT"
                    }
                ],
                "prediction_confidence": 0.85,
                "key_drivers": ["hous_val_amt", "medn_incm_per_prsn_amt", "ppltn_qty"]
            }
        }
    )


class ModelSummaryResponse(BaseModel):
    """Response model for model summary."""
    model_name: str = Field(..., description="Name of the model")
    model_type: str = Field(..., description="Type of model")
    total_features: int = Field(..., description="Total number of features")
    top_5_features: list[str] = Field(..., description="Top 5 most important features")
    explanation_generated: str = Field(..., description="Timestamp when explanation was generated")
