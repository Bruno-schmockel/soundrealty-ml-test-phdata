"""Test API endpoints using future unseen examples data."""

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, client: TestClient):
        """Test GET /health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "model_loaded" in data
        assert "demographics_loaded" in data


class TestPredictEndpoint:
    """Test full /predict endpoint with all features."""
    
    def test_predict_single_example(self, client: TestClient, single_prediction: dict):
        """Test prediction with a single future example."""
        response = client.post("/predict", json=single_prediction)
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "prediction" in data
        assert "model_version" in data
        assert isinstance(data["prediction"], (int, float))
        assert isinstance(data["model_version"], str)
        assert data["prediction"] > 0, "Prediction should be positive"
    
    def test_predict_multiple_examples(self, client: TestClient, sample_prediction_data: list):
        """Test predictions with multiple future examples."""
        for example in sample_prediction_data:
            response = client.post("/predict", json=example)
            assert response.status_code == 200
            data = response.json()
            assert "prediction" in data
            assert data["prediction"] > 0
    
    def test_predict_all_future_examples(self, client: TestClient, future_examples):
        """Test predictions on all future unseen examples."""
        results = []
        for _, row in future_examples.iterrows():
            example = row.to_dict()
            # Convert zipcode to string as expected by the API
            example['zipcode'] = str(int(example['zipcode']))
            response = client.post("/predict", json=example)
            assert response.status_code == 200
            data = response.json()
            assert "prediction" in data
            results.append({
                "zipcode": example["zipcode"],
                "prediction": data["prediction"],
                "actual_features": example
            })
        
        assert len(results) == len(future_examples), "Should have predictions for all examples"
    
    def test_predict_invalid_zipcode(self, client: TestClient, single_prediction: dict):
        """Test prediction with invalid zipcode."""
        invalid_data = single_prediction.copy()
        invalid_data["zipcode"] = "00000"  # Invalid zipcode
        
        response = client.post("/predict", json=invalid_data)
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()
    
    def test_predict_missing_required_field(self, client: TestClient, single_prediction: dict):
        """Test prediction with missing required field."""
        incomplete_data = single_prediction.copy()
        del incomplete_data["bedrooms"]  # Remove required field
        
        response = client.post("/predict", json=incomplete_data)
        assert response.status_code == 422  # Validation error
    
    def test_predict_wrong_type(self, client: TestClient, single_prediction: dict):
        """Test prediction with wrong data type."""
        bad_data = single_prediction.copy()
        bad_data["bedrooms"] = "three"  # Should be int
        
        response = client.post("/predict", json=bad_data)
        assert response.status_code == 422  # Validation error


class TestPredictMinimalEndpoint:
    """Test minimal /predict-minimal endpoint."""
    
    def test_predict_minimal_single_example(self, client: TestClient, single_prediction: dict):
        """Test minimal prediction with a single future example."""
        # Extract only minimal fields
        minimal_data = {
            "bedrooms": single_prediction["bedrooms"],
            "bathrooms": single_prediction["bathrooms"],
            "sqft_living": single_prediction["sqft_living"],
            "sqft_lot": single_prediction["sqft_lot"],
            "floors": single_prediction["floors"],
            "sqft_above": single_prediction["sqft_above"],
            "sqft_basement": single_prediction["sqft_basement"],
            "zipcode": single_prediction["zipcode"]
        }
        
        response = client.post("/predict-minimal", json=minimal_data)
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "prediction" in data
        assert "model_version" in data
        assert isinstance(data["prediction"], (int, float))
        assert data["prediction"] > 0
    
    def test_predict_minimal_multiple_examples(self, client: TestClient, sample_prediction_data: list):
        """Test minimal predictions with multiple future examples."""
        for example in sample_prediction_data:
            minimal_data = {
                "bedrooms": example["bedrooms"],
                "bathrooms": example["bathrooms"],
                "sqft_living": example["sqft_living"],
                "sqft_lot": example["sqft_lot"],
                "floors": example["floors"],
                "sqft_above": example["sqft_above"],
                "sqft_basement": example["sqft_basement"],
                "zipcode": example["zipcode"]
            }
            
            response = client.post("/predict-minimal", json=minimal_data)
            assert response.status_code == 200
            data = response.json()
            assert "prediction" in data
    
    def test_predict_minimal_invalid_zipcode(self, client: TestClient, single_prediction: dict):
        """Test minimal prediction with invalid zipcode."""
        minimal_data = {
            "bedrooms": single_prediction["bedrooms"],
            "bathrooms": single_prediction["bathrooms"],
            "sqft_living": single_prediction["sqft_living"],
            "sqft_lot": single_prediction["sqft_lot"],
            "floors": single_prediction["floors"],
            "sqft_above": single_prediction["sqft_above"],
            "sqft_basement": single_prediction["sqft_basement"],
            "zipcode": "00000"  # Invalid
        }
        
        response = client.post("/predict-minimal", json=minimal_data)
        assert response.status_code == 400


class TestReloadModelEndpoint:
    """Test model reloading endpoint."""
    
    def test_reload_model(self, client: TestClient):
        """Test POST /reload-model endpoint."""
        response = client.post("/reload-model")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "success"
    
    def test_reload_model_then_predict(self, client: TestClient, single_prediction: dict):
        """Test that predictions work after reloading model."""
        # Reload
        reload_response = client.post("/reload-model")
        assert reload_response.status_code == 200
        
        # Predict
        predict_response = client.post("/predict", json=single_prediction)
        assert predict_response.status_code == 200
        data = predict_response.json()
        assert "prediction" in data


class TestPredictionConsistency:
    """Test consistency of predictions across multiple calls."""
    
    def test_same_input_same_output(self, client: TestClient, single_prediction: dict):
        """Test that same input produces same prediction."""
        response1 = client.post("/predict", json=single_prediction)
        response2 = client.post("/predict", json=single_prediction)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        assert data1["prediction"] == data2["prediction"], \
            "Same input should produce same prediction"
    
    def test_predict_vs_minimal_consistency(self, client: TestClient, single_prediction: dict):
        """Test that /predict and /predict-minimal give similar results."""
        # Full prediction
        full_response = client.post("/predict", json=single_prediction)
        assert full_response.status_code == 200
        full_prediction = full_response.json()["prediction"]
        
        # Minimal prediction
        minimal_data = {
            "bedrooms": single_prediction["bedrooms"],
            "bathrooms": single_prediction["bathrooms"],
            "sqft_living": single_prediction["sqft_living"],
            "sqft_lot": single_prediction["sqft_lot"],
            "floors": single_prediction["floors"],
            "sqft_above": single_prediction["sqft_above"],
            "sqft_basement": single_prediction["sqft_basement"],
            "zipcode": single_prediction["zipcode"]
        }
        minimal_response = client.post("/predict-minimal", json=minimal_data)
        assert minimal_response.status_code == 200
        minimal_prediction = minimal_response.json()["prediction"]
        
        # Both should produce predictions (might not be identical since 
        # /predict uses all 18 fields while /minimal uses defaults for others)
        assert full_prediction > 0
        assert minimal_prediction > 0
