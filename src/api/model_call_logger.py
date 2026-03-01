"""Model call logging utilities for tracking predictions."""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path


class ModelCallLogger:
    """Logs detailed information about model predictions with structured logging."""
    
    def __init__(self, log_dir: str = "logs"):
        """Initialize the model call logger.
        
        Args:
            log_dir: Directory to store logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger("model_calls")
        
        # Create file handler for model calls (if not already added)
        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_dir / "model_calls.log")
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log_prediction_call(
        self,
        input_variables: Dict[str, Any],
        model_name: str,
        prediction_result: float,
        caller_metadata: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[float] = None,
        error: Optional[str] = None,
        api_instance_id: Optional[str] = None,
        explanation: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log a model prediction call with all relevant details.
        
        Args:
            input_variables: Dictionary of input features passed to the model
            model_name: Name of the model used for prediction
            prediction_result: The prediction result from the model
            caller_metadata: Optional metadata about the caller (IP, user-agent, etc.)
            execution_time_ms: Optional execution time in milliseconds
            error: Optional error message if prediction failed
            api_instance_id: Optional API instance identifier (container name, hostname, etc.)
            explanation: Optional explanation of the prediction with feature importance
            
        Returns:
            Unique call ID for this prediction
        """
        call_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        log_entry = {
            "call_id": call_id,
            "timestamp": timestamp,
            "api_instance_id": api_instance_id,
            "model_name": model_name,
            "input_variables": input_variables,
            "prediction_result": prediction_result if prediction_result is not None else None,
            "caller_metadata": caller_metadata or {},
            "execution_time_ms": execution_time_ms,
            "error": error,
            "explanation": explanation
        }
        
        # Log to file as structured JSON
        log_message = json.dumps(log_entry)
        if error:
            self.logger.error(f"[{call_id}] {log_message}")
        else:
            self.logger.info(f"[{call_id}] {log_message}")
        
        return call_id
    
    def get_call_summary(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a summary of a previous call by ID.
        
        Note: This is a simple implementation that parses the log file.
        For production, consider using a database.
        
        Args:
            call_id: The unique call ID to look up
            
        Returns:
            Dictionary with call details or None if not found
        """
        log_file = self.log_dir / "model_calls.log"
        if not log_file.exists():
            return None
        
        with open(log_file, 'r') as f:
            for line in f:
                if call_id in line:
                    try:
                        # Extract JSON from log line
                        json_start = line.find('{')
                        if json_start >= 0:
                            json_str = line[json_start:]
                            return json.loads(json_str)
                    except (json.JSONDecodeError, ValueError):
                        pass
        
        return None
