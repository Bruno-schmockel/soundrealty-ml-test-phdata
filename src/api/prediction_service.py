"""Model loading and prediction service."""

import json
import pathlib
import pickle
from typing import Optional, List, Dict, Any
import pandas

from .data_loader import DataLoader


class PredictionService:
    """Handles model loading and making predictions."""

    def __init__(
        self,
        model_path: str = "model/model.pkl",
        features_path: str = "model/model_features.json",
        demographics_path: str = "data/zipcode_demographics.csv"
    ):
        """Initialize prediction service.
        
        Args:
            model_path: Path to pickled model file
            features_path: Path to JSON file with feature names
            demographics_path: Path to demographics CSV file
        """
        self.model_path = pathlib.Path(model_path)
        self.features_path = pathlib.Path(features_path)
        self.data_loader = DataLoader(demographics_path)
        
        self._model = None
        self._features: Optional[List[str]] = None
        self._model_version = "1.0.0"

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
                self._features = json.load(f)
        assert self._features is not None
        return self._features

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
        """Reload model from disk (for hot-deployment)."""
        self._model = None
        self._features = None
        self.load_model()
        self.load_features()
