"""Model loading and prediction service."""

import json
import pathlib
import pickle
import time
from typing import Optional, List, Dict, Any
import numpy as np
import pandas

from .data_loader import DataLoader
from .model_call_logger import ModelCallLogger


class PredictionService:
    """Handles model loading and making predictions."""

    def __init__(
        self,
        model_name: str = "default",
        demographics_path: str = "data/zipcode_demographics.csv"
    ):
        """Initialize prediction service.
        
        Args:
            model_name: Name of the model version to use (will look in model/{model_name}/)
            demographics_path: Path to demographics CSV file
        """
        self.model_name = model_name
        self._set_model_paths(model_name)
        self.data_loader = DataLoader(demographics_path)
        
        self._model = None
        self._features: Optional[List[str]] = None
        self._feature_types: Optional[Dict[str, str]] = None
        self._model_version = model_name
        
        # Initialize model call logger
        self.call_logger = ModelCallLogger()
    
    def _set_model_paths(self, model_name: str) -> None:
        """Set paths based on model name.
        
        Args:
            model_name: Name of the model version
        """
        base_path = pathlib.Path("model") / model_name
        self.model_path = base_path / "model.pkl"
        self.features_path = base_path / "model_features.json"
        self.features_types_path = base_path / "model_features_with_types.json"
    
    def set_model_name(self, model_name: str) -> None:
        """Set the model name and update paths accordingly.
        
        Args:
            model_name: Name of the model version to use
        """
        self.model_name = model_name
        self._set_model_paths(model_name)
        self._model_version = model_name
        # Reset loaded data so they reload from new paths
        self._model = None
        self._features = None
        self._feature_types = None

    def load_model(self) -> None:
        """Load model from disk."""
        with open(self.model_path, 'rb') as f:
            self._model = pickle.load(f)

    def load_features(self) -> List[str]:
        """Load feature list from JSON file.
        
        Returns:
            List of feature names in order
        """
        if self._features is None:
            with open(self.features_path, 'r') as f:
                data = json.load(f)
                # Handle both list format and dict format
                # If dict, use keys as features; if list, use directly
                if isinstance(data, dict):
                    self._features = list(data.keys())
                else:
                    self._features = data
        assert self._features is not None
        return self._features

    def load_feature_types(self) -> Dict[str, str]:
        """Load feature types from JSON file.
        
        Returns:
            Dictionary mapping feature names to their data types
        """
        if self._feature_types is None:
            # Try to load from features_with_types file
            try:
                with open(self.features_types_path, 'r') as f:
                    self._feature_types = json.load(f)
            except FileNotFoundError:
                # Fallback: if features_with_types doesn't exist, return empty dict
                self._feature_types = {}
        assert self._feature_types is not None
        return self._feature_types

    def is_ready(self) -> bool:
        """Check if model and features are loaded.
        
        Returns:
            True if both model and features are loaded
        """
        return self._model is not None and self._features is not None

    def predict(
        self,
        bedrooms: int,
        bathrooms: float,
        sqft_living: int,
        sqft_lot: int,
        floors: float,
        sqft_above: int,
        sqft_basement: int,
        zipcode: str
    ) -> Dict[str, Any]:
        """Make a prediction for a home.
        
        Args:
            bedrooms: Number of bedrooms
            bathrooms: Number of bathrooms
            sqft_living: Living area in sqft
            sqft_lot: Lot area in sqft
            floors: Number of floors
            sqft_above: Sqft above ground
            sqft_basement: Sqft of basement
            zipcode: 5-digit zipcode
            
        Returns:
            Dictionary with prediction and metadata
            
        Raises:
            RuntimeError: If model is not loaded
            KeyError: If required features are missing
        """
        # Lazy load model and features if not already loaded
        if self._model is None:
            self.load_model()
        if self._features is None:
            self.load_features()
        
        if not self.is_ready():
            raise RuntimeError("Failed to load prediction model. Check that model/feature files exist and are valid.")
        
        # Type guard: after is_ready() passes, model and features are guaranteed to exist
        assert self._model is not None
        assert self._features is not None

        # Get demographics data for zipcode (O(1) dict lookup)
        zipcode_demo = self.data_loader.get_demographics_for_zipcode(zipcode)
        if zipcode_demo is None:
            raise ValueError(f"Zipcode {zipcode} not found in demographics database")

        # Combine input features with demographics into single dict
        input_dict = {
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'sqft_living': sqft_living,
            'sqft_lot': sqft_lot,
            'floors': floors,
            'sqft_above': sqft_above,
            'sqft_basement': sqft_basement,
        }
        
        # Add demographics fields (excluding zipcode which is not a model feature)
        for key, value in zipcode_demo.items():
            if key != 'zipcode':
                input_dict[key] = value

        # Get features in correct order and create DataFrame with only required columns
        features = self.load_features()
        input_data = pandas.DataFrame([{feature: input_dict.get(feature) for feature in features}])


        # Make prediction
        prediction = self._model.predict(input_data)[0]

        return {
            "prediction": float(prediction),
            "model_version": self._model_version,
            "confidence": None  # Could be enhanced with model confidence
        }

    def reload_model(self) -> None:
        """Reload model and data from disk (for hot-deployment)."""
        self._model = None
        self._features = None
        self._feature_types = None
        self.load_model()
        self.load_features()
        self.load_feature_types()
        self.data_loader.reload_demographics()

    def validate_input(self, input_dict: dict) -> None:
        """Validate that all required model features are present in input with correct types.
        
        Args:
            input_dict: Dictionary of input values
            
        Raises:
            ValueError: If required features are missing, have None values, or have wrong types
        """
        features = self.load_features()
        feature_types = self.load_feature_types()
        
        # Check for missing features
        missing_features = [f for f in features if f not in input_dict]
        if missing_features:
            raise ValueError(
                f"Missing required features: {', '.join(missing_features)}. "
                f"Expected features: {', '.join(features)}"
            )
        
        # Check for None values in required fields
        none_values = [f for f in features if input_dict.get(f) is None]
        if none_values:
            raise ValueError(
                f"Invalid or missing values for features: {', '.join(none_values)}"
            )
        
        # Type validation if feature types are available
        if feature_types:
            type_errors = []
            for feature in features:
                expected_type = feature_types.get(feature)
                if expected_type:
                    value = input_dict[feature]
                    # Map numpy/pandas types to Python types for validation
                    if 'int' in expected_type and not isinstance(value, (int, np.integer)):
                        type_errors.append(f"  {feature}: expected {expected_type}, got {type(value).__name__}")
                    elif 'float' in expected_type and not isinstance(value, (int, float, np.number)):
                        type_errors.append(f"  {feature}: expected {expected_type}, got {type(value).__name__}")
            
            if type_errors:
                raise ValueError(
                    "Type mismatch in input data:\n" + "\n".join(type_errors)
                )

    def predict_from_dict(self, input_dict: dict, caller_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a prediction using a dictionary of input values.
        
        Assumes input has been validated. Extracts only required fields
        and makes the prediction. This approach is independent of specific field names.
        Logs all prediction details including input, output, and caller metadata.
        
        Args:
            input_dict: Dictionary containing all required input values (should be pre-validated)
            caller_metadata: Optional metadata about the caller (IP address, user agent, etc.)
            
        Returns:
            Dictionary with prediction and metadata
        """
        # Extract only the features required by the model in the correct order
        features = self.load_features()
        ordered_features = {f: input_dict[f] for f in features}
        
        # Create DataFrame with features in the correct order
        input_data = pandas.DataFrame([ordered_features])
        
        # Lazy load model if needed
        if self._model is None:
            self.load_model()
        
        assert self._model is not None
        
        # Record start time for execution tracking
        start_time = time.time()
        
        # Make prediction
        prediction = self._model.predict(input_data)[0]
        
        # Calculate execution time
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Log the prediction call with all details
        call_id = self.call_logger.log_prediction_call(
            input_variables=input_dict,
            model_name=self.model_name,
            prediction_result=float(prediction),
            caller_metadata=caller_metadata,
            execution_time_ms=execution_time_ms
        )
        
        return {
            "prediction": float(prediction),
            "model_name": self.model_name,
            "call_id": call_id
        }
