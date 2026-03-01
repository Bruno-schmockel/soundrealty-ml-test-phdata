"""Test error logging in model call logger."""

import requests
import json

BASE_URL = "http://localhost"

def test_invalid_zipcode():
    """Test prediction with an invalid zipcode."""
    
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
        "zipcode": "99999",  # Invalid zipcode
        "lat": 47.5,
        "long": -122.3,
        "sqft_living15": 1800,
        "sqft_lot15": 5000
    }
    
    print("Testing /predict endpoint with INVALID ZIPCODE...")
    print(f"Zipcode: 99999 (should not exist in database)")
    
    try:
        response = requests.post(
            f"{BASE_URL}/predict",
            json=payload,
            headers={"User-Agent": "TestErrorClient/1.0"}
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code != 200:
            print(f"\n✓ Error correctly returned (Status {response.status_code})")
        
    except Exception as e:
        print(f"Error during request: {e}")


def test_missing_field():
    """Test prediction with missing required field."""
    
    payload = {
        "bedrooms": 3,
        "bathrooms": 2.0,
        "sqft_living": 2000,
        "sqft_lot": 5000,
        "floors": 2.0,
        # Missing sqft_above - required field
        "sqft_basement": 500,
        "yr_built": 2000,
        "yr_renovated": 0,
        "zipcode": "98001",
        "lat": 47.5,
        "long": -122.3,
        "sqft_living15": 1800,
        "sqft_lot15": 5000
    }
    
    print("\n\nTesting /predict endpoint with MISSING REQUIRED FIELD...")
    print("Missing: sqft_above")
    
    try:
        response = requests.post(
            f"{BASE_URL}/predict",
            json=payload,
            headers={"User-Agent": "TestErrorClient/1.0"}
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code != 200:
            print(f"\n✓ Error correctly detected (Status {response.status_code})")
        
    except Exception as e:
        print(f"Error during request: {e}")


if __name__ == "__main__":
    print("=" * 70)
    print("ERROR HANDLING TEST SUITE")
    print("=" * 70)
    
    test_invalid_zipcode()
    test_missing_field()
    
    print("\n" + "=" * 70)
    print("Check container logs for error logging:")
    print("  docker exec soundrealty-api-basic cat /app/logs/model_calls.log")
    print("=" * 70)
