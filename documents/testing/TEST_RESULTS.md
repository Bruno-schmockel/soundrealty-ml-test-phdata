# Test Suite Results & Deployment Status

## Summary
✅ **ALL 39 TESTS PASSING**
✅ **MODEL SWITCHING TESTS COMPLETE**
✅ **DOCKER CONTAINERIZATION READY**
✅ **API FULLY OPERATIONAL**
✅ **MULTIPLE MODELS SUPPORTED**

- **API Endpoint Tests**: 14/14 passing ✅
- **Model Switching Tests**: 12/12 passing ✅
- **Prediction Service Tests**: 13/13 passing ✅  
- **Total Coverage**: 39 test cases across API endpoints, model switching, and ML prediction logic
- **Supported Models**: `basic` and `added_features`
- **Environment**: Python 3.9.23 (housing conda)  
- **Test Response Format**: Simplified with `prediction` and `model_name` fields

---

## Test Execution

### Local Testing (Recommended for Development)

**Run all tests with default model (basic):**
```bash
conda activate housing
pytest src/tests/
```

**Run tests with specific model version:**
```bash
conda activate housing
pytest src/tests/ --model-name=basic
pytest src/tests/ --model-name=added_features
```

**Run with verbose output:**
```bash
conda activate housing
pytest src/tests/ -v
pytest src/tests/ -v --model-name=added_features
```

**Run specific test file:**
```bash
# Test model switching between basic and added_features
pytest src/tests/test_model_switching.py -v

# Test API endpoints
pytest src/tests/test_api_endpoints.py -v

# Test prediction service
pytest src/tests/test_prediction_service.py -v
```

### Docker Testing (For Containerized Verification)

**Deploy container with specific model version:**
```bash
# Deploy with default model (basic)
docker-compose up -d

# Or deploy with specific model version
docker-compose run -e MODEL_NAME=basic soundrealty-api

# Or modify docker-compose.yml and set MODEL_NAME in environment section
```

**Run tests inside the Docker container:**
```bash
# Start the container first
docker-compose up -d

# Run tests in the container
docker-compose exec soundrealty-api pytest src/tests/

# Run tests with specific model
docker-compose exec soundrealty-api pytest src/tests/ --model-name=basic

# Or use curl to test endpoints directly
curl http://localhost:8000/health
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{...}'
```

---

## Test Coverage Details

### Model Switching Tests (test_model_switching.py)

New comprehensive test suite for validating model switching between `basic` and `added_features` models.

#### TestModelSwitching (8 tests)
- `test_basic_model_loads`: Basic model loads correctly with health check
- `test_added_features_model_loads`: Added features model loads correctly with health check  
- `test_basic_model_prediction`: Basic model produces valid predictions
- `test_added_features_model_prediction`: Added features model produces valid predictions
- `test_models_produce_different_predictions`: Different models produce different predictions for same input
- `test_response_includes_model_name`: Response correctly identifies which model was used
- `test_both_models_handle_multiple_predictions`: Both models handle batch predictions consistently
- `test_consistency_within_model`: Same model produces identical predictions for duplicate requests

#### TestModelValidation (4 tests)
- `test_invalid_zipcode_basic_model`: Basic model rejects invalid zipcodes (400 error)
- `test_invalid_zipcode_added_features_model`: Added features model rejects invalid zipcodes (400 error)
- `test_missing_field_basic_model`: Basic model validates required fields (422 error)
- `test_missing_field_added_features_model`: Added features model validates required fields (422 error)

**Total: 12 Model switching tests**

---

### API Endpoint Tests (test_api_endpoints.py)

#### TestHealthEndpoint (1 test)
- `test_health_check`: Verifies health endpoint returns correct status with model and demographics loaded

#### TestPredictEndpoint (6 tests)
- `test_predict_single_example`: Single home prediction with full request (includes high-correlation features: grade, sqft_living15)
- `test_predict_multiple_examples`: Batch predictions with 5 homes
- `test_predict_all_future_examples`: All 100 future examples processed successfully
- `test_predict_invalid_zipcode`: Returns 400 error for invalid zipcodes
- `test_predict_missing_required_field`: Returns 422 validation error for missing fields
- `test_predict_wrong_type`: Rejects incorrect data types

#### TestPredictMinimalEndpoint (3 tests)
- `test_predict_minimal_single_example`: Single prediction with 8 core fields (uses basic model)
- `test_predict_minimal_multiple_examples`: Batch predictions with minimal input
- `test_predict_minimal_invalid_zipcode`: Returns 400 error for invalid zipcodes

#### TestReloadModelEndpoint (2 tests)
- `test_reload_model`: Model reloading endpoint works correctly
- `test_reload_model_then_predict`: Predictions work after model reload

#### TestPredictionConsistency (2 tests)
- `test_same_input_same_output`: Same input produces same prediction across calls
- `test_predict_vs_minimal_consistency`: /predict and /predict-minimal return same results for overlapping fields

**Total: 14 API endpoint tests**

**Response Format:**
All prediction endpoints return a simplified, clean JSON response:
```json
{
  "prediction": 425000.50,
  "model_name": "added_features"
}
```
- `prediction`: Float - predicted home price in USD
- `model_name`: String - identifies which model produced the prediction (basic or added_features)

---

---

### Prediction Service Tests (test_prediction_service.py)

#### TestPredictionServiceInitialization (5 tests)
- `test_service_initialization`: Service instantiates correctly
- `test_model_loading`: Model loads from disk
- `test_features_loading`: Feature list loads from JSON
- `test_is_ready_before_loading`: `is_ready()` returns False initially
- `test_is_ready_after_loading`: `is_ready()` returns True after loading

#### TestPredictionServicePredictions (4 tests)
- `test_predict_basic`: Basic prediction functionality works
- `test_predict_returns_float`: Predictions are numeric
- `test_predict_different_inputs_different_outputs`: Different homes get different prices
- `test_predict_invalid_zipcode`: Raises exception for invalid zipcodes

#### TestPredictionServiceWithFutureExamples (2 tests)
- `test_predict_all_future_examples`: All 100 future examples can be predicted
- `test_first_future_example`: First future example produces valid prediction

#### TestDataLoaderIntegration (2 tests)
- `test_demographics_loading`: Demographics data loads and has zipcode column
- `test_valid_zipcode_check`: Zipcode validation works correctly

**Total: 13 Prediction service tests**

---

## Data Coverage

The test suite validates predictions across:
- **100 future unseen examples** from `data/future_unseen_examples.csv`
- **45 unique zipcodes** in the King County area
- **Full 18-field request schema** validation
- **Minimal 8-field request schema** validation
- **Edge cases**: Invalid zipcodes, missing fields, wrong data types

---

## Key Test Features

✅ **Model Switching**: Tests validate behavior switching between `basic` and `added_features` models
✅ **High-Correlation Features**: Added_features model includes grade (0.667) and sqft_living15 (0.585)
✅ **Different Predictions**: Confirms models produce measurably different predictions due to different features
✅ **All 4 API Endpoints**: Tests /health, /predict, /predict-minimal
✅ **Uses Real Future Data**: Tests with 100 actual unseen examples from CSV
✅ **Input Validation**: Tests all expected validations and error handling
✅ **Prediction Consistency**: Confirms same model produces identical results for duplicate requests
✅ **Demographics Integration**: Validates zipcode-based demographic data lookup
✅ **Response Format**: Simplified JSON with prediction and model_name only
✅ **Both Happy & Error Paths**: Tests success cases and error conditions

---

## Known Warnings

The test output includes sklearn version mismatch warnings (not failures):
- `InconsistentVersionWarning`: Models trained with sklearn 1.3.1, running on 1.7.2
- **Impact**: None - tests pass, models function correctly
- **Recommendation**: Consider retraining models with current sklearn version for production

---

## Continuous Integration

To run tests in CI/CD pipeline:
```bash
conda activate housing
python -m pytest src/tests/ -v --tb=short
```

---

## Requirements for Test Execution

All dependencies are installed in the `housing` conda environment:
- fastapi>=0.128.0
- pydantic>=2.12.0
- pytest>=8.4.2
- httpx>=0.28.0
- scikit-learn>=1.3.0
- pandas>=2.1.0
- uvicorn>=0.35.0

Activate the environment:
```bash
conda activate housing
```

---

## Model Information

### Basic Model
- **Features**: 9 core features (bedrooms, bathrooms, sqft_living, sqft_lot, floors, sqft_above, sqft_basement, zipcode demographics)
- **Algorithm**: K-Nearest Neighbors with RobustScaler
- **Purpose**: Minimal viable model with essential features
- **Location**: `model/basic/`

### Added Features Model  
- **Features**: 11 features (basic + `grade` + `sqft_living15`)
- **High-Correlation Additions**:
  - `grade`: Building quality (0.667 correlation with price)
  - `sqft_living15`: Living area of 15 nearest neighbors (0.585 correlation)
- **Algorithm**: K-Nearest Neighbors with RobustScaler
- **Purpose**: Improved model with features identified through correlation analysis
- **Location**: `model/added_features/`


