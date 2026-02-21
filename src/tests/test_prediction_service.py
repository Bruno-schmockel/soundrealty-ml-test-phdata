"""Unit tests for prediction service."""

import pytest
import sys
import pathlib
from src.api.prediction_service import PredictionService

# Add src directory to path
src_path = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(src_path.parent))




class TestPredictionServiceInitialization:
    """Test PredictionService initialization and loading."""
    
    def test_service_initialization(self):
        """Test that service initializes without errors."""
        service = PredictionService()
        assert service._model is None
        assert service._features is None
    
    def test_model_loading(self):
        """Test model loading."""
        service = PredictionService()
        service.load_model()
        assert service._model is not None
    
    def test_features_loading(self):
        """Test features loading."""
        service = PredictionService()
        service.load_features()
        features = service.load_features()
        assert isinstance(features, list)
        assert len(features) > 0
        assert all(isinstance(f, str) for f in features)
    
    def test_is_ready_before_loading(self):
        """Test is_ready returns False before loading."""
        service = PredictionService()
        assert not service.is_ready()
    
    def test_is_ready_after_loading(self):
        """Test is_ready returns True after loading."""
        service = PredictionService()
        service.load_model()
        service.load_features()
        assert service.is_ready()


class TestPredictionServicePredictions:
    """Test prediction functionality."""
    
    @pytest.fixture
    def service(self):
        """Initialize and load service."""
        service = PredictionService()
        service.load_model()
        service.load_features()
        return service
    
    def test_predict_basic(self, service: PredictionService):
        """Test basic prediction."""
        result = service.predict(
            bedrooms=3,
            bathrooms=2.0,
            sqft_living=2000,
            sqft_lot=5000,
            floors=2.0,
            sqft_above=1500,
            sqft_basement=500,
            zipcode="98001"
        )
        
        assert "prediction" in result
        assert "model_version" in result
        assert result["prediction"] > 0
    
    def test_predict_returns_float(self, service: PredictionService):
        """Test that prediction returns float value."""
        result = service.predict(
            bedrooms=4,
            bathrooms=2.5,
            sqft_living=2200,
            sqft_lot=6000,
            floors=1.5,
            sqft_above=1660,
            sqft_basement=560,
            zipcode="98115"
        )
        
        assert isinstance(result["prediction"], float)
    
    def test_predict_different_inputs_different_outputs(self, service: PredictionService):
        """Test that different inputs produce different predictions."""
        result1 = service.predict(
            bedrooms=2,
            bathrooms=1.0,
            sqft_living=1000,
            sqft_lot=3000,
            floors=1.0,
            sqft_above=1000,
            sqft_basement=0,
            zipcode="98001"
        )
        
        result2 = service.predict(
            bedrooms=5,
            bathrooms=3.0,
            sqft_living=4000,
            sqft_lot=8000,
            floors=2.5,
            sqft_above=3000,
            sqft_basement=1000,
            zipcode="98001"
        )
        
        # Larger/nicer home should cost more
        assert result2["prediction"] > result1["prediction"]
    
    def test_predict_invalid_zipcode(self, service: PredictionService):
        """Test prediction with invalid zipcode."""
        with pytest.raises(Exception):  # Should raise an error
            service.predict(
                bedrooms=3,
                bathrooms=2.0,
                sqft_living=2000,
                sqft_lot=5000,
                floors=2.0,
                sqft_above=1500,
                sqft_basement=500,
                zipcode="00000"  # Invalid
            )


class TestPredictionServiceWithFutureExamples:
    """Test prediction service with future unseen examples."""
    
    @pytest.fixture
    def service(self):
        """Initialize and load service."""
        service = PredictionService()
        service.load_model()
        service.load_features()
        return service
    
    def test_predict_all_future_examples(self, service: PredictionService, future_examples):
        """Test predictions on all future examples."""
        predictions = []
        
        for _, row in future_examples.iterrows():
            result = service.predict(
                bedrooms=int(row["bedrooms"]),
                bathrooms=float(row["bathrooms"]),
                sqft_living=int(row["sqft_living"]),
                sqft_lot=int(row["sqft_lot"]),
                floors=float(row["floors"]),
                sqft_above=int(row["sqft_above"]),
                sqft_basement=int(row["sqft_basement"]),
                zipcode=str(int(row["zipcode"]))
            )
            
            assert result["prediction"] > 0
            predictions.append(result["prediction"])
        
        # Verify we got predictions for all examples
        assert len(predictions) == len(future_examples)
        
        # Verify predictions are reasonable (typical home prices)
        min_price = min(predictions)
        max_price = max(predictions)
        assert min_price > 50000, "Minimum prediction seems too low"
        assert max_price < 10000000, "Maximum prediction seems too high"
    
    def test_first_future_example(self, service: PredictionService, single_prediction: dict):
        """Test prediction on first future example."""
        result = service.predict(
            bedrooms=int(single_prediction["bedrooms"]),
            bathrooms=float(single_prediction["bathrooms"]),
            sqft_living=int(single_prediction["sqft_living"]),
            sqft_lot=int(single_prediction["sqft_lot"]),
            floors=float(single_prediction["floors"]),
            sqft_above=int(single_prediction["sqft_above"]),
            sqft_basement=int(single_prediction["sqft_basement"]),
            zipcode=str(single_prediction["zipcode"])
        )
        
        assert result["prediction"] > 0
        assert result["model_version"] == "1.0.0"


class TestDataLoaderIntegration:
    """Test data loader integration with prediction service."""
    
    def test_demographics_loading(self):
        """Test that demographics are loaded correctly."""
        service = PredictionService()
        demographics = service.data_loader.load_demographics()
        
        assert demographics is not None
        assert len(demographics) > 0
        assert "zipcode" in demographics.columns
    
    def test_valid_zipcode_check(self):
        """Test valid zipcode checking."""
        service = PredictionService()
        service.data_loader.load_demographics()
        
        # Should accept any zipcode from the future examples
        assert service.data_loader.is_valid_zipcode("98001")
        assert service.data_loader.is_valid_zipcode("98115")
        assert not service.data_loader.is_valid_zipcode("00000")
