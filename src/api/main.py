from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
import logging

from .models import (
    PredictionRequest,
    PredictionMinimalRequest,
    PredictionResponse,
    HealthResponse
)
from .prediction_service import PredictionService


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize prediction service
prediction_service = PredictionService(
    model_path="model/model.pkl",
    features_path="model/model_features.json",
    features_types_path="model/model_features_with_types.json",
    demographics_path="data/zipcode_demographics.csv"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model and data on startup, cleanup on shutdown."""
    # Startup code
    try:
        logger.info("Loading model...")
        prediction_service.load_model()
        logger.info("Loading features...")
        prediction_service.load_features()
        logger.info("Loading feature types...")
        prediction_service.load_feature_types()
        logger.info("Loading demographics data...")
        prediction_service.data_loader.load_demographics()
        logger.info("All models and data loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load: {e}")
        raise
    
    yield
    
    # Shutdown code (cleanup if needed)
    logger.info("Shutting down API")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Sound Realty Prediction API",
    description="REST API for predicting home prices using an ML model",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint to verify service status."""
    return {
        "status": "healthy",
        "model_loaded": prediction_service._model is not None,
        "demographics_loaded": prediction_service.data_loader._demographics_by_zipcode is not None
    }


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Predict home price using full set of features.
    
    This endpoint accepts all available features including zipcode,
    automatically joins demographic data, and returns a price prediction.
    """
    # Validate zipcode and get demographics in one call
    zipcode_demo = prediction_service.data_loader.get_demographics_for_zipcode(request.zipcode)
    if zipcode_demo is None:
        raise HTTPException(
            status_code=400,
            detail=f"Zipcode {request.zipcode} not found in demographics database"
        )

    try:
        # Build input data dynamically from request fields
        input_data = request.model_dump()
        # Remove zipcode as it's not a model feature, but get demographics instead
        del input_data['zipcode']
        # Add demographics fields
        for key, value in zipcode_demo.items():
            if key != 'zipcode':
                input_data[key] = value
        
        # Validate input data against model features
        prediction_service.validate_input(input_data)
        
        # Make prediction
        result = prediction_service.predict_from_dict(input_data)
        return result

    except ValueError as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except KeyError as e:
        logger.error(f"Missing required features: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Missing required feature: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/predict-minimal", response_model=PredictionResponse)
async def predict_minimal(request: PredictionMinimalRequest):
    """
    Predict home price using minimal feature set.
    
    Bonus endpoint: accepts only the core features required by the model,
    automatically joins demographic data by zipcode.
    """
    # Validate zipcode and get demographics in one call
    zipcode_demo = prediction_service.data_loader.get_demographics_for_zipcode(request.zipcode)
    if zipcode_demo is None:
        raise HTTPException(
            status_code=400,
            detail=f"Zipcode {request.zipcode} not found in demographics database"
        )

    try:
        # Build input data dynamically from request fields
        input_data = request.model_dump()
        # Remove zipcode as it's not a model feature, but get demographics instead
        del input_data['zipcode']
        # Add demographics fields
        for key, value in zipcode_demo.items():
            if key != 'zipcode':
                input_data[key] = value
        
        # Validate input data against model features
        prediction_service.validate_input(input_data)
        
        # Make prediction
        result = prediction_service.predict_from_dict(input_data)
        return result

    except ValueError as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except KeyError as e:
        logger.error(f"Missing required features: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Missing required feature: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/reload-model")
async def reload_model():
    """
    Reload model from disk without restarting service.
    
    Allows deployment of new model versions without downtime.
    This endpoint can be called by a deployment system when a new model is available.
    Also reloads demographics data to ensure consistency.
    """
    try:
        logger.info("Reloading model...")
        logger.info("Reloading demographics data...")
        prediction_service.reload_model()
        logger.info("Model and data reloaded successfully")
        return {"status": "success", "message": "Model and data reloaded"}
    except Exception as e:
        logger.error(f"Failed to reload model: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reload model: {str(e)}")