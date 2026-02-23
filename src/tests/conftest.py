"""Pytest configuration and fixtures for API tests."""

import sys
import os
import pathlib
import pandas
import pytest

# Add project root and src to path
project_root = pathlib.Path(__file__).parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

# Set working directory for relative paths
os.chdir(project_root)

# Set default MODEL_NAME before importing app (will be overridden by pytest_configure if --model-name is provided)
if 'MODEL_NAME' not in os.environ:
    os.environ['MODEL_NAME'] = 'basic'


def pytest_addoption(parser):
    """Add custom command-line options to pytest."""
    parser.addoption(
        "--model-name",
        action="store",
        default=None,
        help="Model name to use for testing (e.g., 'basic')"
    )


def pytest_configure(config):
    """Configure pytest with custom options."""
    # Get model name from --model-name option or MODEL_NAME env var, default to 'basic'
    model_name = config.getoption("--model-name") or os.getenv('MODEL_NAME', 'basic')
    os.environ['MODEL_NAME'] = model_name
    # Store in config for access by fixtures
    config.model_name = model_name


# Import after configuration is complete
from fastapi.testclient import TestClient  # noqa: E402
from api.main import app  # noqa: E402


@pytest.fixture
def model_name(request):
    """Get the model name being tested."""
    return request.config.model_name


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def future_examples():
    """Load future unseen examples from CSV."""
    csv_path = project_root / "data" / "future_unseen_examples.csv"
    return pandas.read_csv(csv_path)


@pytest.fixture
def sample_prediction_data(future_examples):
    """Get first 5 rows from future examples as test data."""
    rows = future_examples.head(5)
    data = []
    for _, row in rows.iterrows():
        row_dict = row.to_dict()
        # Convert zipcode to string as expected by the API
        row_dict['zipcode'] = str(int(row_dict['zipcode']))
        data.append(row_dict)
    return data


@pytest.fixture
def single_prediction(future_examples):
    """Get first row from future examples as single test case."""
    row = future_examples.iloc[0]
    row_dict = row.to_dict()
    # Convert zipcode to string as expected by the API
    row_dict['zipcode'] = str(int(row_dict['zipcode']))
    return row_dict
