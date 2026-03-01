from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
import logging
import os

from .models import (
    PredictionRequest,
    PredictionMinimalRequest,
    PredictionResponse,
    HealthResponse,
    PredictionExplanationResponse,
    ModelSummaryResponse
)
from .prediction_service import PredictionService
from .model_explainer import ModelExplainer


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get model name from environment variable (default to 'basic' if not set)
MODEL_NAME = os.getenv('MODEL_NAME', 'basic')

# Initialize prediction service (respects MODEL_NAME environment variable)
prediction_service = PredictionService(
    model_name=MODEL_NAME,
    demographics_path="data/zipcode_demographics.csv"
)

# Initialize basic model service for /predict-minimal (always uses 'basic')
basic_model_service = PredictionService(
    model_name='basic',
    demographics_path="data/zipcode_demographics.csv"
)

# Initialize model explainer for generating prediction explanations
model_explainer = ModelExplainer(model_dir="model")


def extract_caller_metadata(request: Request) -> dict:
    """Extract metadata about the caller from the request.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Dictionary containing caller metadata
    """
    client_host = request.client.host if request.client else "unknown"
    client_port = request.client.port if request.client else None
    user_agent = request.headers.get("user-agent", "unknown")
    
    return {
        "client_ip": client_host,
        "client_port": client_port,
        "user_agent": user_agent,
        "endpoint": request.url.path,
        "method": request.method
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model and data on startup, cleanup on shutdown."""
    # Startup code
    try:
        logger.info(f"Loading main model ({MODEL_NAME})...")
        prediction_service.load_model()
        logger.info("Loading features...")
        prediction_service.load_features()
        logger.info("Loading feature types...")
        prediction_service.load_feature_types()
        logger.info("Loading demographics data...")
        prediction_service.data_loader.load_demographics()
        
        logger.info("Loading basic model for minimal endpoint...")
        basic_model_service.load_model()
        basic_model_service.load_features()
        basic_model_service.load_feature_types()
        
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
async def predict(request: PredictionRequest, http_request: Request):
    """
    Predict home price using full set of features.
    
    This endpoint accepts all available features including zipcode,
    automatically joins demographic data, and returns a price prediction.
    """
    # Extract caller metadata for logging
    caller_metadata = extract_caller_metadata(http_request)
    
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
        
        # Filter input data to only include features the model was trained with
        expected_features = set(prediction_service.load_features())
        filtered_input_data = {k: v for k, v in input_data.items() if k in expected_features}
        
        # Validate input data against model features
        prediction_service.validate_input(filtered_input_data)
        
        # Make prediction with caller metadata and endpoint identification
        result = prediction_service.predict_from_dict(
            filtered_input_data, 
            caller_metadata=caller_metadata,
            api_instance_id="predict"
        )
        
        # Generate explanation only if model is not 'basic' and has explanation artifacts
        explanation_summary = None
        if prediction_service.model_name != 'basic' and prediction_service.model_name in model_explainer.explanation_cache:
            explanation = model_explainer.get_prediction_explanation(
                model_name=prediction_service.model_name,
                input_dict=filtered_input_data,
                prediction=result['prediction']
            )
            
            # Create simplified explanation summary for response
            explanation_summary = {
                "prediction_confidence": explanation.get('prediction_confidence'),
                "key_drivers": explanation.get('key_drivers'),
                "top_features": [
                    {
                        "feature": f['feature'],
                        "importance": f['importance'],
                        "z_score": f['z_score']
                    }
                    for f in explanation.get('feature_analysis', [])[:5]
                ]
            }
            
            # Add explanation to result
            result['explanation'] = explanation_summary
        
        # Log prediction with explanation (if available)
        prediction_service.call_logger.log_prediction_call(
            input_variables=filtered_input_data,
            model_name=prediction_service.model_name,
            prediction_result=result['prediction'],
            caller_metadata=caller_metadata,
            execution_time_ms=result.get('execution_time_ms'),
            api_instance_id="predict",
            explanation=explanation_summary
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
async def predict_minimal(request: PredictionMinimalRequest, http_request: Request):
    """
    Predict home price using minimal feature set with the basic model.
    
    Bonus endpoint: accepts only the core features required by the model,
    automatically joins demographic data by zipcode.
    Always uses the 'basic' model regardless of MODEL_NAME environment variable.
    """
    # Extract caller metadata for logging
    caller_metadata = extract_caller_metadata(http_request)
    
    # Validate zipcode and get demographics in one call
    zipcode_demo = basic_model_service.data_loader.get_demographics_for_zipcode(request.zipcode)
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
        
        # Filter input data to only include features the model was trained with
        expected_features = set(basic_model_service.load_features())
        filtered_input_data = {k: v for k, v in input_data.items() if k in expected_features}
        
        # Validate input data against model features
        basic_model_service.validate_input(filtered_input_data)
        
        # Make prediction with caller metadata and endpoint identification
        result = basic_model_service.predict_from_dict(
            filtered_input_data, 
            caller_metadata=caller_metadata,
            api_instance_id="predict-minimal"
        )
        
        # Generate explanation only if model is not 'basic' and has explanation artifacts
        explanation_summary = None
        if basic_model_service.model_name != 'basic' and basic_model_service.model_name in model_explainer.explanation_cache:
            explanation = model_explainer.get_prediction_explanation(
                model_name=basic_model_service.model_name,
                input_dict=filtered_input_data,
                prediction=result['prediction']
            )
            
            # Create simplified explanation summary for response
            explanation_summary = {
                "prediction_confidence": explanation.get('prediction_confidence'),
                "key_drivers": explanation.get('key_drivers'),
                "top_features": [
                    {
                        "feature": f['feature'],
                        "importance": f['importance'],
                        "z_score": f['z_score']
                    }
                    for f in explanation.get('feature_analysis', [])[:5]
                ]
            }
            
            # Add explanation to result
            result['explanation'] = explanation_summary
        
        # Log prediction with explanation (if available)
        basic_model_service.call_logger.log_prediction_call(
            input_variables=filtered_input_data,
            model_name=basic_model_service.model_name,
            prediction_result=result['prediction'],
            caller_metadata=caller_metadata,
            execution_time_ms=result.get('execution_time_ms'),
            api_instance_id="predict-minimal",
            explanation=explanation_summary
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
async def reload_model(model_name: str = "basic"):
    """
    Reload model from disk without restarting service.
    
    Args:
        model_name: Name of the model to reload for /predict endpoint (defaults to 'basic').
    
    Updates only the model used by the /predict endpoint.
    The /predict-minimal endpoint always uses the fixed 'basic' model.
    
    Allows deployment of new model versions without downtime.
    This endpoint can be called by a deployment system when a new model is available.
    """
    try:
        logger.info(f"Reloading model '{model_name}' for /predict endpoint...")
        prediction_service.set_model_name(model_name)
        prediction_service.reload_model()
        logger.info(f"Model '{model_name}' reloaded successfully")
        return {"status": "success", "message": f"Model '{model_name}' reloaded for /predict endpoint"}
    except Exception as e:
        logger.error(f"Failed to reload model '{model_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reload model: {str(e)}")


@app.post("/explain", response_model=PredictionExplanationResponse)
async def explain_prediction(request: PredictionRequest):
    """
    Get an explanation for a prediction without saving it.
    
    Returns an explanation of which features drove the prediction and how unusual
    the input values are compared to the training data.
    """
    # Validate zipcode and get demographics
    zipcode_demo = prediction_service.data_loader.get_demographics_for_zipcode(request.zipcode)
    if zipcode_demo is None:
        raise HTTPException(
            status_code=400,
            detail=f"Zipcode {request.zipcode} not found in demographics database"
        )

    try:
        # Build input data
        input_data = request.model_dump()
        del input_data['zipcode']
        for key, value in zipcode_demo.items():
            if key != 'zipcode':
                input_data[key] = value
        
        # Validate and predict
        prediction_service.validate_input(input_data)
        prediction_result = prediction_service.predict_from_dict(
            input_data,
            api_instance_id="explain"
        )
        
        # Get explanation
        explanation = model_explainer.get_prediction_explanation(
            model_name=prediction_service.model_name,
            input_dict=input_data,
            prediction=prediction_result['prediction']
        )
        
        return explanation

    except ValueError as e:
        logger.error(f"Explanation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in explanation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/model-info", response_model=ModelSummaryResponse)
async def get_model_info():
    """
    Get information about the currently active model.
    
    Returns model type, total features, and the top 5 most important features.
    """
    summary = model_explainer.get_model_summary(prediction_service.model_name)
    
    if "error" in summary:
        raise HTTPException(status_code=404, detail=summary["error"])
    
    return summary


@app.get("/feature-importance")
async def get_feature_importance(top_n: int = 10):
    """
    Get feature importance rankings for the current model.
    
    Args:
        top_n: Number of top features to return (default 10)
        
    Returns:
        List of features ranked by importance
    """
    features = model_explainer.get_feature_importance(
        prediction_service.model_name,
        top_n=top_n
    )
    
    if not features:
        raise HTTPException(
            status_code=404,
            detail=f"No feature importance data found for model '{prediction_service.model_name}'"
        )
    
    return {
        "model_name": prediction_service.model_name,
        "feature_count": len(features),
        "top_features": features
    }
