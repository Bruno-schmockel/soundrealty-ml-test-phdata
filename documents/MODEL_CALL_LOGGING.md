# Model Call Logging Implementation

## Overview
Added comprehensive logging to the API model prediction calls to track all relevant information about each prediction request including input variables, model used, results, execution time, and caller metadata.

## Components Added

### 1. Model Call Logger (`src/api/model_call_logger.py`)
New module that provides the `ModelCallLogger` class responsible for:
- Generating unique IDs for each prediction call
- Logging prediction details to structured JSON format
- Storing logs in a `logs/` directory
- Providing retrieval functionality for specific call records

**Key Features:**
- Unique call IDs (UUID format) for tracking individual predictions
- Structured JSON logging for easy parsing and analysis
- Separate log file (`logs/model_calls.log`) for model calls
- Retrieval capability to look up past calls by ID

### 2. Updated Prediction Service (`src/api/prediction_service.py`)
Enhanced the prediction service to:
- Initialize the `ModelCallLogger` on startup
- Capture execution time for each prediction
- Log all prediction calls with complete metadata
- Return the unique call ID to the caller

**Changes to `predict_from_dict()` method:**
- Added optional `caller_metadata` parameter
- Records start and end time to calculate execution time in milliseconds
- Logs input variables, model name, prediction result, and caller metadata
- Returns call ID along with prediction results

### 3. Updated API Endpoints (`src/api/main.py`)
Enhanced both prediction endpoints to:
- Extract caller metadata from HTTP requests
- Pass metadata to the prediction service
- Return the call ID in responses

**New helper function `extract_caller_metadata(request: Request)`:**
Extracts and returns:
- Client IP address
- Client port
- User-Agent header
- Endpoint path
- HTTP method

**Updated endpoints:**
- `/predict` - Now captures caller metadata and passes it to prediction service
- `/predict-minimal` - Now captures caller metadata and passes it to prediction service

### 4. Updated Response Model (`src/api/models.py`)
Modified `PredictionResponse` to include:
- `call_id`: Unique identifier for tracking the prediction call

## Logged Information

Each prediction call logs the following information in JSON format:

```json
{
  "call_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-03-01T15:30:45.123456",
  "model_name": "added_features",
  "input_variables": {
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
    "lat": 47.5,
    "long": -122.3,
    "sqft_living15": 1800,
    "sqft_lot15": 5000,
    "population": 45000,
    "median_age": 38.5,
    "median_income": 85000.0
  },
  "prediction_result": 425000.50,
  "caller_metadata": {
    "client_ip": "192.168.1.100",
    "client_port": 54321,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "endpoint": "/predict",
    "method": "POST"
  },
  "execution_time_ms": 45.23,
  "error": null
}
```

## Usage

### Making a Prediction
When you call either `/predict` or `/predict-minimal` endpoints, the response will include a `call_id`:

```json
{
  "prediction": 425000.50,
  "model_name": "added_features",
  "call_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Viewing Logs
Logs are stored in `logs/model_calls.log` in JSON format. Each line is a complete log entry.

### Programmatic Access
You can retrieve call details using the logger's `get_call_summary()` method:

```python
from src.api.model_call_logger import ModelCallLogger

logger = ModelCallLogger()
call_details = logger.get_call_summary("550e8400-e29b-41d4-a716-446655440000")
```

## Benefits

1. **Audit Trail**: Complete record of all predictions made through the API
2. **Debugging**: Execute time information helps identify performance issues
3. **Monitoring**: Caller IP addresses enable network/load analysis
4. **Compliance**: Detailed logs for regulatory or business requirements
5. **Performance Analysis**: Execution time tracking helps optimize model serving
6. **User Tracking**: IP and user-agent information for request tracing

## Log Directory Structure
```
logs/
  model_calls.log     # All model prediction calls in JSON format
```

## Future Enhancements
- Add database backend for more robust log storage and querying
- Implement log rotation for long-running services
- Add metrics collection (prediction distribution, latency percentiles)
- Implement real-time monitoring/alerting based on log patterns
- Add optional encryption for sensitive features in logs
