"""Script to display formatted log entries from model_calls.log."""

import json
import subprocess
import sys

def get_logs_from_container():
    """Retrieve logs from the Docker container."""
    try:
        result = subprocess.run(
            ["docker", "exec", "soundrealty-api-basic", "cat", "/app/logs/model_calls.log"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error reading logs: {e}")
        return None


def parse_log_entry(line):
    """Parse a log line and extract the JSON portion."""
    if " - INFO - " in line:
        json_part = line.split(" - INFO - ", 1)[1]
        # Remove the call_id prefix like "[uuid] "
        if "] " in json_part:
            json_part = json_part.split("] ", 1)[1]
        return json.loads(json_part)
    return None


def display_log(log_data):
    """Display log data in a nice format."""
    print("\n" + "=" * 80)
    print("MODEL CALL LOG ENTRY")
    print("=" * 80)
    
    print(f"\n📊 Call ID:        {log_data['call_id']}")
    print(f"⏰ Timestamp:      {log_data['timestamp']}")
    print(f"🤖 Model:         {log_data['model_name']}")
    print(f"⚡ Execution:     {log_data['execution_time_ms']:.2f} ms")
    
    print("\n📥 INPUT FEATURES:")
    input_vars = log_data['input_variables']
    # Show just the core features, not all demographics
    core_features = ['bedrooms', 'bathrooms', 'sqft_living', 'sqft_lot', 'floors', 
                     'sqft_above', 'sqft_basement', 'waterfront', 'view', 'condition']
    for feature in core_features:
        if feature in input_vars:
            print(f"   • {feature}: {input_vars[feature]}")
    
    print(f"\n📤 PREDICTION RESULT: ${log_data['prediction_result']:,.2f}")
    
    print("\n👤 CALLER METADATA:")
    metadata = log_data['caller_metadata']
    print(f"   • IP Address:     {metadata['client_ip']}")
    print(f"   • Port:           {metadata['client_port']}")
    print(f"   • User-Agent:     {metadata['user_agent']}")
    print(f"   • Endpoint:       {metadata['endpoint']}")
    print(f"   • Method:         {metadata['method']}")
    
    if log_data['error']:
        print(f"\n❌ Error:         {log_data['error']}")
    else:
        print(f"\n✓ Status:         Success")


if __name__ == "__main__":
    print("=" * 80)
    print("RETRIEVING AND DISPLAYING MODEL CALL LOGS")
    print("=" * 80)
    
    logs_content = get_logs_from_container()
    
    if not logs_content:
        print("No logs found!")
        sys.exit(1)
    
    # Parse and display each log entry
    log_lines = logs_content.strip().split('\n')
    
    for i, line in enumerate(log_lines, 1):
        if line.strip():
            try:
                log_data = parse_log_entry(line)
                if log_data:
                    display_log(log_data)
            except json.JSONDecodeError as e:
                print(f"Error parsing line {i}: {e}")
    
    print("\n" + "=" * 80)
    print(f"TOTAL LOGS: {len([l for l in log_lines if l.strip()])}")
    print("=" * 80)
