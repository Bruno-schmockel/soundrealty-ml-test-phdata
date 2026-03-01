"""Test script for verifying model call logging in the API."""

import requests
import json
import time

BASE_URL = "http://localhost"

def test_predict_endpoint():
    """Test the /predict endpoint and verify logging."""
    
    payload = {
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
    
    print("Testing /predict endpoint...")
    print(f"Sending request with payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/predict",
            json=payload,
            headers={"User-Agent": "TestClient/1.0"}
        )
        
        print(f"\nResponse Status: {response.status_code}")
        response_data = response.json()
        print(f"Response Data:\n{json.dumps(response_data, indent=2)}")
        
        call_id = response_data.get("call_id")
        if call_id:
            print(f"\n✓ Unique Call ID received: {call_id}")
        else:
            print("\n✗ No Call ID in response")
        
        return call_id
    except Exception as e:
        print(f"Error during request: {e}")
        return None


def test_predict_minimal_endpoint():
    """Test the /predict-minimal endpoint."""
    
    payload = {
        "bedrooms": 4,
        "bathrooms": 3.0,
        "sqft_living": 3000,
        "sqft_lot": 6000,
        "floors": 2.0,
        "sqft_above": 2000,
        "sqft_basement": 1000,
        "zipcode": "98109"
    }
    
    print("\n\nTesting /predict-minimal endpoint...")
    print(f"Sending request with payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/predict-minimal",
            json=payload,
            headers={"User-Agent": "TestClient/1.0"}
        )
        
        print(f"\nResponse Status: {response.status_code}")
        response_data = response.json()
        print(f"Response Data:\n{json.dumps(response_data, indent=2)}")
        
        call_id = response_data.get("call_id")
        if call_id:
            print(f"\n✓ Unique Call ID received: {call_id}")
        else:
            print("\n✗ No Call ID in response")
        
        return call_id
    except Exception as e:
        print(f"Error during request: {e}")
        return None


def test_health_endpoint():
    """Test the health endpoint."""
    
    print("Testing /health endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Response Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("MODEL CALL LOGGING TEST SUITE")
    print("=" * 70)
    
    # Test health endpoint first
    if not test_health_endpoint():
        print("\nHealth check failed. Exiting...")
        exit(1)
    
    time.sleep(1)
    
    # Test prediction endpoints
    call_id_1 = test_predict_endpoint()
    time.sleep(1)
    call_id_2 = test_predict_minimal_endpoint()
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"✓ Health check: PASSED")
    print(f"✓ /predict endpoint: {'PASSED' if call_id_1 else 'FAILED'}")
    print(f"✓ /predict-minimal endpoint: {'PASSED' if call_id_2 else 'FAILED'}")
    
    if call_id_1 or call_id_2:
        print("\n✓ Logging appears to be working (call_ids returned)")
        print("Check the container logs for model_calls.log file verification")
