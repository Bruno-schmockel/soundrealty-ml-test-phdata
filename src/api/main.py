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
        # Make prediction
        result = prediction_service.predict(
            bedrooms=request.bedrooms,
            bathrooms=request.bathrooms,
            sqft_living=request.sqft_living,
            sqft_lot=request.sqft_lot,
            floors=request.floors,
            sqft_above=request.sqft_above,
            sqft_basement=request.sqft_basement,
            zipcode=request.zipcode
        )

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
        # Make prediction with default values for optional fields
        result = prediction_service.predict(
            bedrooms=request.bedrooms,
            bathrooms=request.bathrooms,
            sqft_living=request.sqft_living,
            sqft_lot=request.sqft_lot,
            floors=request.floors,
            sqft_above=request.sqft_above,
            sqft_basement=request.sqft_basement,
            zipcode=request.zipcode
        )

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
    """
    try:
        logger.info("Reloading model...")
        prediction_service.reload_model()
        logger.info("Model reloaded successfully")
        return {"status": "success", "message": "Model reloaded"}
    except Exception as e:
        logger.error(f"Failed to reload model: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reload model: {str(e)}")