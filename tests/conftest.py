import pytest
import os
import sys
from unittest.mock import MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_ehr_data():
    return {
        "patient_id": "P001",
        "demographics": {"age": 68, "gender": "Male"},
        "conditions": [{"name": "Type 2 Diabetes", "status": "Active"}],
        "vitals": {"bp": "130/80", "hr": 72}
    }

@pytest.fixture
def mock_labs_data():
    return {
        "patient_id": "P001",
        "results": [
            {"test": "Hemoglobin A1c", "value": 7.2, "unit": "%", "status": "High"}
        ]
    }

@pytest.fixture
def mock_meds_data():
    return {
        "patient_id": "P001",
        "active": [
            {"name": "Metformin", "dosage": "1000mg", "frequency": "BID"}
        ]
    }
