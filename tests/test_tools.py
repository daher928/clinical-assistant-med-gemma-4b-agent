import pytest
from unittest.mock import patch, mock_open
import json
from tools import ehr, labs, meds

@pytest.mark.asyncio
async def test_get_ehr(mock_ehr_data):
    with patch("builtins.open", mock_open(read_data=json.dumps(mock_ehr_data))):
        with patch("os.path.exists", return_value=True):
            data = await ehr.get_ehr("P001")
            assert data["patient_id"] == "P001"
            assert data["demographics"]["age"] == 68

@pytest.mark.asyncio
async def test_get_labs(mock_labs_data):
    with patch("builtins.open", mock_open(read_data=json.dumps(mock_labs_data))):
        with patch("os.path.exists", return_value=True):
            data = await labs.get_labs("P001")
            assert len(data["results"]) == 1
            assert data["results"][0]["test"] == "Hemoglobin A1c"

@pytest.mark.asyncio
async def test_get_meds(mock_meds_data):
    with patch("builtins.open", mock_open(read_data=json.dumps(mock_meds_data))):
        with patch("os.path.exists", return_value=True):
            data = await meds.get_meds("P001")
            assert len(data["active"]) == 1
            assert data["active"][0]["name"] == "Metformin"

@pytest.mark.asyncio
async def test_file_not_found():
    with patch("os.path.exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            await ehr.get_ehr("INVALID_ID")
