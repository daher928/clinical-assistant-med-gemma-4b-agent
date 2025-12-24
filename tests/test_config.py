import os
import pytest
from config import Settings

def test_default_config():
    """Test default configuration values."""
    config = Settings()
    assert config.MODEL_ID == "google/medgemma-4b-it"
    assert config.USE_MOCK_LLM is False
    assert config.DATA_DIR == "demo_data"
    assert config.EHR_DIR == "demo_data/ehr"

def test_env_override(monkeypatch):
    """Test environment variable overrides."""
    monkeypatch.setenv("USE_MOCK_LLM", "true")
    monkeypatch.setenv("MODEL_ID", "custom-model")
    
    config = Settings()
    assert config.USE_MOCK_LLM is True
    assert config.MODEL_ID == "custom-model"

def test_device_detection_override():
    """Test device override logic."""
    config = Settings(DEVICE_OVERRIDE="cpu")
    assert config.get_device() == "cpu"
    
    config = Settings(DEVICE_OVERRIDE="cuda")
    assert config.get_device() == "cuda"
