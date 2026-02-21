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

# Import after path is set
from fastapi.testclient import TestClient
from api.main import app


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
