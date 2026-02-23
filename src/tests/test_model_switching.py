"""Test that models can be switched between basic and added_features."""

import os
import sys
import pathlib
import pytest
from fastapi.testclient import TestClient

# Add project root and src to path
project_root = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))
os.chdir(project_root)


def create_client_with_model(model_name):
    """Create a new FastAPI test client with a specific model loaded."""
    # Set the environment variable before importing the app
    os.environ['MODEL_NAME'] = model_name
    
    # Clear any cached imports to force reload
    if 'api.main' in sys.modules:
        del sys.modules['api.main']
    if 'api.prediction_service' in sys.modules:
        del sys.modules['api.prediction_service']
    
    # Import fresh app instance
    from api.main import app, prediction_service
    
    # Manually load the model and data since TestClient doesn't invoke lifespan properly
    try:
        prediction_service.load_model()
        prediction_service.load_features()
        prediction_service.load_feature_types()
        prediction_service.data_loader.load_demographics()
    except Exception as e:
        print(f"Warning: Failed to load model data: {e}")
    
    return TestClient(app)


class TestModelSwitching:
    """Test switching between different models."""
    
    def test_basic_model_loads(self):
        """Test that the basic model loads correctly."""
        client = create_client_with_model('basic')
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["model_loaded"] is True
    
    def test_added_features_model_loads(self):
        """Test that the added_features model loads correctly."""
        client = create_client_with_model('added_features')
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["model_loaded"] is True
    
    def test_basic_model_prediction(self, single_prediction):
        """Test prediction using basic model."""
        client = create_client_with_model('basic')
        response = client.post("/predict", json=single_prediction)
        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data
        assert data["prediction"] > 0
        assert "model_name" in data
        assert data["model_name"] == "basic"
        return data["prediction"]
    
    def test_added_features_model_prediction(self, single_prediction):
        """Test prediction using added_features model."""
        client = create_client_with_model('added_features')
        response = client.post("/predict", json=single_prediction)
        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data
        assert data["prediction"] > 0
        assert "model_name" in data
        assert data["model_name"] == "added_features"
        return data["prediction"]
    
    def test_models_produce_different_predictions(self, single_prediction):
        """Test that basic and added_features models produce different predictions."""
        # Get prediction from basic model
        basic_client = create_client_with_model('basic')
        basic_response = basic_client.post("/predict", json=single_prediction)
        basic_prediction = basic_response.json()["prediction"]
        
        # Get prediction from added_features model
        added_features_client = create_client_with_model('added_features')
        added_features_response = added_features_client.post("/predict", json=single_prediction)
        added_features_prediction = added_features_response.json()["prediction"]
        
        # Models should produce different predictions due to different features
        # Allow small numerical differences due to floating point precision
        assert abs(basic_prediction - added_features_prediction) > 1, \
            f"Predictions too similar: basic={basic_prediction}, added_features={added_features_prediction}"
    
    def test_response_includes_model_name(self, single_prediction):
        """Test that response includes model_name field."""
        for model_name in ['basic', 'added_features']:
            client = create_client_with_model(model_name)
            response = client.post("/predict", json=single_prediction)
            assert response.status_code == 200
            data = response.json()
            assert "model_name" in data, f"Response missing model_name for {model_name}"
            assert data["model_name"] == model_name, \
                f"Expected model_name={model_name}, got {data['model_name']}"
            assert "prediction" in data
    
    def test_both_models_handle_multiple_predictions(self, sample_prediction_data):
        """Test that both models can handle multiple predictions."""
        models = ['basic', 'added_features']
        
        for model_name in models:
            client = create_client_with_model(model_name)
            predictions = []
            
            for example in sample_prediction_data:
                response = client.post("/predict", json=example)
                assert response.status_code == 200
                data = response.json()
                assert "prediction" in data
                assert "model_name" in data
                assert data["model_name"] == model_name
                predictions.append(data["prediction"])
            
            assert len(predictions) == len(sample_prediction_data), \
                f"Model {model_name} should produce predictions for all examples"
    
    def test_consistency_within_model(self, single_prediction):
        """Test that same model produces consistent predictions across calls."""
        client = create_client_with_model('added_features')
        
        predictions = []
        model_names = []
        for _ in range(3):
            response = client.post("/predict", json=single_prediction)
            data = response.json()
            predictions.append(data["prediction"])
            model_names.append(data["model_name"])
        
        # All predictions should be identical
        assert predictions[0] == predictions[1] == predictions[2], \
            "Same model should produce identical predictions for same input"
        
        # All should report the same model name
        assert all(name == 'added_features' for name in model_names), \
            "All responses should report model_name as 'added_features'"


class TestModelValidation:
    """Test validation and error handling across models."""
    
    def test_invalid_zipcode_basic_model(self, single_prediction):
        """Test that basic model rejects invalid zipcode."""
        client = create_client_with_model('basic')
        invalid_data = single_prediction.copy()
        invalid_data["zipcode"] = "00000"
        
        response = client.post("/predict", json=invalid_data)
        assert response.status_code == 400
    
    def test_invalid_zipcode_added_features_model(self, single_prediction):
        """Test that added_features model rejects invalid zipcode."""
        client = create_client_with_model('added_features')
        invalid_data = single_prediction.copy()
        invalid_data["zipcode"] = "00000"
        
        response = client.post("/predict", json=invalid_data)
        assert response.status_code == 400
    
    def test_missing_field_basic_model(self, single_prediction):
        """Test that basic model rejects missing fields."""
        client = create_client_with_model('basic')
        incomplete_data = single_prediction.copy()
        del incomplete_data["bedrooms"]
        
        response = client.post("/predict", json=incomplete_data)
        assert response.status_code == 422
    
    def test_missing_field_added_features_model(self, single_prediction):
        """Test that added_features model rejects missing fields."""
        client = create_client_with_model('added_features')
        incomplete_data = single_prediction.copy()
        del incomplete_data["bedrooms"]
        
        response = client.post("/predict", json=incomplete_data)
        assert response.status_code == 422


def pytest_generate_tests(metafunc):
    """Parametrize tests to run with both models."""
    if "model_name_param" in metafunc.fixturenames:
        metafunc.parametrize("model_name_param", ["basic", "added_features"])


@pytest.fixture
def single_prediction():
    """Get first row from future examples as single test case."""
    import pandas
    csv_path = project_root / "data" / "future_unseen_examples.csv"
    future_examples = pandas.read_csv(csv_path)
    row = future_examples.iloc[0]
    row_dict = row.to_dict()
    # Convert zipcode to string as expected by the API
    row_dict['zipcode'] = str(int(row_dict['zipcode']))
    return row_dict


@pytest.fixture
def sample_prediction_data():
    """Get first 5 rows from future examples as test data."""
    import pandas
    csv_path = project_root / "data" / "future_unseen_examples.csv"
    future_examples = pandas.read_csv(csv_path)
    rows = future_examples.head(5)
    data = []
    for _, row in rows.iterrows():
        row_dict = row.to_dict()
        # Convert zipcode to string as expected by the API
        row_dict['zipcode'] = str(int(row_dict['zipcode']))
        data.append(row_dict)
    return data
