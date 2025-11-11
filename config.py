"""
Configuration management for Clinical Assistant Agent.
"""
import os
import torch


class Config:
    """Central configuration class."""
    
    # Model settings
    MODEL_ID = os.getenv("MODEL_ID", "google/medgemma-4b-it")
    USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "false").lower() == "true"
    
    # Device detection
    @staticmethod
    def get_device():
        """Auto-detect the best available device."""
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            # MPS has 4GB temp array limit - may fail with large models
            # Uncomment next line to force CPU if you hit MPS errors
            return "mps"  # Force CPU to avoid MPS limitations
            # return "mps"
        else:
            return "cpu"
    
    # Generation parameters (balanced for MedGemma compatibility)

    # Data directories
    DATA_DIR = "demo_data"
    EHR_DIR = f"{DATA_DIR}/ehr"
    LABS_DIR = f"{DATA_DIR}/labs"
    MEDS_DIR = f"{DATA_DIR}/meds"
    IMAGING_DIR = f"{DATA_DIR}/imaging"
    DRUGS_DIR = f"{DATA_DIR}/drugs"
    GUIDELINES_DIR = f"{DATA_DIR}/guidelines"
    
    # Prompts
    SYSTEM_PROMPT_PATH = "prompts/system.txt"

