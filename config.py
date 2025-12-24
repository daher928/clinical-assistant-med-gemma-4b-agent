"""
Configuration management for Clinical Assistant Agent.
"""
import os
import torch
from typing import Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field


class Settings(BaseSettings):
    """Central configuration class using Pydantic."""
    
    # Model settings
    MODEL_ID: str = Field(default="google/medgemma-4b-it", description="HuggingFace model ID")
    USE_MOCK_LLM: bool = Field(default=False, description="Use mock LLM instead of real model")
    
    # Generation parameters
    MAX_NEW_TOKENS: int = Field(default=500, description="Max new tokens for generation")
    TEMPERATURE: float = Field(default=0.7, description="Sampling temperature")
    TOP_P: float = Field(default=0.9, description="Top-p sampling")
    
    # Gemini API
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="API key for Gemini")
    
    # Device override (optional)
    DEVICE_OVERRIDE: Optional[str] = Field(default=None, description="Force specific device (cuda, mps, cpu)")

    # Data directories
    DATA_DIR: str = "demo_data"
    
    @computed_field
    def EHR_DIR(self) -> str:
        return f"{self.DATA_DIR}/ehr"
        
    @computed_field
    def LABS_DIR(self) -> str:
        return f"{self.DATA_DIR}/labs"
        
    @computed_field
    def MEDS_DIR(self) -> str:
        return f"{self.DATA_DIR}/meds"
        
    @computed_field
    def IMAGING_DIR(self) -> str:
        return f"{self.DATA_DIR}/imaging"
        
    @computed_field
    def DRUGS_DIR(self) -> str:
        return f"{self.DATA_DIR}/drugs"
        
    @computed_field
    def GUIDELINES_DIR(self) -> str:
        return f"{self.DATA_DIR}/guidelines"

    # Prompts
    SYSTEM_PROMPT_PATH: str = "prompts/system.txt"

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_device(self) -> str:
        """
        Auto-detect the best available device with explicit override support.
        """
        # 1. Check for explicit override
        if self.DEVICE_OVERRIDE:
            return self.DEVICE_OVERRIDE.lower()
            
        # 2. Check CUDA
        if torch.cuda.is_available():
            return "cuda"
            
        # 3. Check MPS (Apple Silicon)
        # Note: MPS has known issues with some ops, but is generally faster than CPU
        if torch.backends.mps.is_available():
            # Optional: Check for specific OS version or constraints if needed
            return "mps"
            
        # 4. Fallback to CPU
        return "cpu"


# Global singleton instance
Config = Settings()

