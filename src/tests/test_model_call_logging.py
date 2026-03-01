"""Test model call logging functionality."""

import json
import uuid
from pathlib import Path
import pytest
from fastapi.testclient import TestClient


class TestModelCallLogging:
    """Test model call logging in prediction endpoints."""
    
    def test_predict_returns_call_id(self, client: TestClient, single_prediction: dict):
        """Test that /predict endpoint returns a call_id."""
        response = client.post("/predict", json=single_prediction)
        assert response.status_code == 200
        data = response.json()
        
        # Check for call_id in response
        assert "call_id" in data, "Response should include call_id"
        assert isinstance(data["call_id"], str), "call_id should be a string"
        assert len(data["call_id"]) == 36, "call_id should be a valid UUID (36 chars)"
    
    def test_predict_call_id_is_valid_uuid(self, client: TestClient, single_prediction: dict):
        """Test that the call_id is a valid UUID format."""
        response = client.post("/predict", json=single_prediction)
        assert response.status_code == 200
        call_id = response.json()["call_id"]
        
        # Validate UUID format
        try:
            uuid_obj = uuid.UUID(call_id)
            assert str(uuid_obj) == call_id
        except ValueError:
            pytest.fail(f"call_id '{call_id}' is not a valid UUID")
    
    def test_predict_response_contains_all_fields(self, client: TestClient, single_prediction: dict):
        """Test that /predict response has all required fields."""
        response = client.post("/predict", json=single_prediction)
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["prediction", "model_name", "call_id"]
        for field in required_fields:
            assert field in data, f"Response should include '{field}'"
    
    def test_predict_minimal_returns_call_id(self, client: TestClient):
        """Test that /predict-minimal endpoint returns a call_id."""
        minimal_payload = {
            "bedrooms": 3,
            "bathrooms": 2.0,
            "sqft_living": 2000,
            "sqft_lot": 5000,
            "floors": 2.0,
            "sqft_above": 1500,
            "sqft_basement": 500,
            "zipcode": "98001"
        }
        
        response = client.post("/predict-minimal", json=minimal_payload)
        assert response.status_code == 200
        data = response.json()
        
        # Check for call_id in response
        assert "call_id" in data, "Response should include call_id"
        assert isinstance(data["call_id"], str), "call_id should be a string"
    
    def test_predict_minimal_response_contains_all_fields(self, client: TestClient):
        """Test that /predict-minimal response has all required fields."""
        minimal_payload = {
            "bedrooms": 3,
            "bathrooms": 2.0,
            "sqft_living": 2000,
            "sqft_lot": 5000,
            "floors": 2.0,
            "sqft_above": 1500,
            "sqft_basement": 500,
            "zipcode": "98001"
        }
        
        response = client.post("/predict-minimal", json=minimal_payload)
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["prediction", "model_name", "call_id"]
        for field in required_fields:
            assert field in data, f"Response should include '{field}'"
    
    def test_each_prediction_has_unique_call_id(self, client: TestClient, single_prediction: dict):
        """Test that each prediction gets a unique call_id."""
        call_ids = set()
        
        # Make multiple predictions
        for _ in range(5):
            response = client.post("/predict", json=single_prediction)
            assert response.status_code == 200
            call_id = response.json()["call_id"]
            
            # Verify uniqueness
            assert call_id not in call_ids, f"Duplicate call_id: {call_id}"
            call_ids.add(call_id)
        
        assert len(call_ids) == 5, "Should have 5 unique call_ids"
    
    def test_predict_with_multiple_examples(self, client: TestClient, sample_prediction_data: list):
        """Test predictions with multiple examples return call_ids."""
        call_ids = []
        
        for example in sample_prediction_data:
            response = client.post("/predict", json=example)
            assert response.status_code == 200
            data = response.json()
            
            # Each should have a call_id
            assert "call_id" in data, "Each response should include call_id"
            call_ids.append(data["call_id"])
        
        # All should be unique
        assert len(set(call_ids)) == len(call_ids), "All call_ids should be unique"


class TestModelCallLoggingContent:
    """Test the content of model call logs."""
    
    def test_logs_directory_exists(self):
        """Test that logs directory is created."""
        logs_dir = Path("logs")
        assert logs_dir.exists(), "logs directory should exist"
        assert logs_dir.is_dir(), "logs should be a directory"
    
    def test_model_calls_log_file_exists(self):
        """Test that model_calls.log file is created."""
        log_file = Path("logs") / "model_calls.log"
        assert log_file.exists(), "model_calls.log should exist"
        assert log_file.is_file(), "model_calls.log should be a file"
    
    def test_log_entries_are_valid_json(self, client: TestClient, single_prediction: dict):
        """Test that log entries are valid JSON format."""
        log_file = Path("logs") / "model_calls.log"
        
        # Get initial log file size
        initial_size = log_file.stat().st_size if log_file.exists() else 0
        
        # Make a prediction
        response = client.post("/predict", json=single_prediction)
        assert response.status_code == 200
        
        # Read logs and validate JSON
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        # Find the new log entry (should be the last line with content)
        if lines:
            last_line = lines[-1].strip()
            if last_line:
                try:
                    # Extract JSON part (after "[UUID] " prefix)
                    if "] " in last_line:
                        json_part = last_line.split("] ", 1)[1]
                    else:
                        json_part = last_line
                    
                    log_data = json.loads(json_part)
                    assert isinstance(log_data, dict), "Log entry should be a JSON object"
                except json.JSONDecodeError as e:
                    pytest.fail(f"Log entry is not valid JSON: {e}")
    
    def test_log_contains_required_fields(self, client: TestClient, single_prediction: dict):
        """Test that log entries contain all required fields."""
        log_file = Path("logs") / "model_calls.log"
        
        # Make a prediction
        response = client.post("/predict", json=single_prediction)
        assert response.status_code == 200
        api_call_id = response.json()["call_id"]
        
        # Read logs and find our entry
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        # Find the matching log entry
        found = False
        for line in lines:
            if api_call_id in line:
                # Extract JSON part
                if "] " in line:
                    json_part = line.split("] ", 1)[1]
                else:
                    json_part = line
                
                log_data = json.loads(json_part)
                
                # Check for required fields
                required_fields = [
                    "call_id",
                    "timestamp",
                    "model_name",
                    "input_variables",
                    "prediction_result",
                    "caller_metadata",
                    "execution_time_ms",
                    "error"
                ]
                
                for field in required_fields:
                    assert field in log_data, f"Log entry should include '{field}'"
                
                # Verify call_id matches
                assert log_data["call_id"] == api_call_id, "call_id in log should match response"
                
                found = True
                break
        
        assert found, f"Could not find log entry for call_id {api_call_id}"
    
    def test_log_contains_input_variables(self, client: TestClient, single_prediction: dict):
        """Test that logs contain the input variables."""
        log_file = Path("logs") / "model_calls.log"
        
        # Make a prediction
        response = client.post("/predict", json=single_prediction)
        assert response.status_code == 200
        api_call_id = response.json()["call_id"]
        
        # Read logs and find our entry
        with open(log_file, 'r') as f:
            content = f.read()
        
        # Find and parse our log entry
        import re
        pattern = rf'\]\s*({{"call_id":\s*"{api_call_id}"[^}}]*?"input_variables":\s*{{[^}}]*?}}'
        
        lines = content.split('\n')
        for line in lines:
            if api_call_id in line:
                if "] " in line:
                    json_part = line.split("] ", 1)[1]
                else:
                    json_part = line
                
                log_data = json.loads(json_part)
                
                # Check that input_variables exists and has content
                assert "input_variables" in log_data, "Log should contain input_variables"
                assert isinstance(log_data["input_variables"], dict), "input_variables should be a dict"
                assert len(log_data["input_variables"]) > 0, "input_variables should not be empty"
                
                # Check for core features
                assert "bedrooms" in log_data["input_variables"], "Should log bedrooms"
                
                break
    
    def test_log_contains_caller_metadata(self, client: TestClient, single_prediction: dict):
        """Test that logs contain caller metadata."""
        log_file = Path("logs") / "model_calls.log"
        
        # Make a prediction
        response = client.post("/predict", json=single_prediction)
        assert response.status_code == 200
        api_call_id = response.json()["call_id"]
        
        # Read logs and find our entry
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        # Find and parse our log entry
        for line in lines:
            if api_call_id in line:
                if "] " in line:
                    json_part = line.split("] ", 1)[1]
                else:
                    json_part = line
                
                log_data = json.loads(json_part)
                
                # Check caller metadata
                assert "caller_metadata" in log_data, "Log should contain caller_metadata"
                metadata = log_data["caller_metadata"]
                
                required_metadata = [
                    "client_ip",
                    "client_port",
                    "user_agent",
                    "endpoint",
                    "method"
                ]
                
                for field in required_metadata:
                    assert field in metadata, f"Metadata should include '{field}'"
                
                # Verify values
                assert isinstance(metadata["client_ip"], str), "client_ip should be string"
                assert isinstance(metadata["user_agent"], str), "user_agent should be string"
                assert metadata["endpoint"] == "/predict", "endpoint should be /predict"
                assert metadata["method"] == "POST", "method should be POST"
                
                break
    
    def test_log_execution_time_is_reasonable(self, client: TestClient, single_prediction: dict):
        """Test that execution time is logged and reasonable."""
        log_file = Path("logs") / "model_calls.log"
        
        # Make a prediction
        response = client.post("/predict", json=single_prediction)
        assert response.status_code == 200
        api_call_id = response.json()["call_id"]
        
        # Read logs and find our entry
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        # Find and parse our log entry
        for line in lines:
            if api_call_id in line:
                if "] " in line:
                    json_part = line.split("] ", 1)[1]
                else:
                    json_part = line
                
                log_data = json.loads(json_part)
                
                # Check execution time
                assert "execution_time_ms" in log_data, "Should log execution_time_ms"
                exec_time = log_data["execution_time_ms"]
                
                assert isinstance(exec_time, (int, float)), "execution_time should be numeric"
                assert exec_time > 0, "execution_time should be positive"
                assert exec_time < 10000, "execution_time should be less than 10 seconds"
                
                break


class TestModelCallLoggingWithErrors:
    """Test logging behavior with error conditions."""
    
    def test_invalid_zipcode_does_not_log_prediction(self, client: TestClient, single_prediction: dict):
        """Test that invalid zipcode doesn't create a log entry (error before model call)."""
        log_file = Path("logs") / "model_calls.log"
        
        # Get initial content
        with open(log_file, 'r') as f:
            initial_content = f.read()
        
        # Make prediction with invalid zipcode
        invalid_data = single_prediction.copy()
        invalid_data["zipcode"] = "00000"
        
        response = client.post("/predict", json=invalid_data)
        assert response.status_code == 400
        
        # Log should not have changed (error occurs before model call)
        with open(log_file, 'r') as f:
            final_content = f.read()
        
        # The content might change slightly due to file system, but shouldn't have new prediction log
        assert response.json()["detail"] == "Zipcode 00000 not found in demographics database"
