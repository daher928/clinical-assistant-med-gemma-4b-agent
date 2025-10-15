"""
MedGemma LLM wrapper for clinical decision support.

This module implements a singleton pattern with lazy loading to ensure
the model is only loaded once and reused across requests.
"""
import json
import torch
from typing import Optional, Dict
from config import Config


class MockLLM:
    """Mock LLM - Uses template generator for intelligent, accurate summaries."""
    
    def synthesize(self, system_prompt: str, user_prompt: str, observations: Dict) -> str:
        """Generate intelligent clinical summary using template engine."""
        
        # Extract patient_id and complaint from user_prompt
        patient_id = "unknown"
        complaint = "clinical evaluation"
        
        if "patient_id:" in user_prompt:
            patient_id = user_prompt.split("patient_id:")[1].split("\n")[0].strip()
        if "complaint:" in user_prompt:
            complaint = user_prompt.split("complaint:")[1].strip().strip('"')
        
        # Use template generator for intelligent summary
        try:
            from agent.template_generator import TemplateSummaryGenerator
            result = TemplateSummaryGenerator.generate_from_data(
                observations, patient_id, complaint
            )
            
            return result
            
        except Exception as e:
            # Fallback to basic summary
            ehr = observations.get('EHR', {})
            demographics = ehr.get('demographics', {})
            age = demographics.get('age', 'Unknown')
            gender = demographics.get('gender', 'Unknown')
            conditions = [c.get('name', '') for c in ehr.get('conditions', [])]
            
            return f"""## ONE-LINE SUMMARY
{age}yo {gender} presenting with {complaint}

## PATIENT SNAPSHOT
- {age}yo {gender}
- Conditions: {', '.join(conditions) if conditions else 'None documented'}

## ATTENTION NEEDED
- Unable to generate detailed analysis

## PLAN
1. Review patient data manually
2. Contact technical support if issue persists"""


class MedGemmaLLM:
    """
    Singleton wrapper for MedGemma language model with lazy loading.
    
    This class ensures the model is only loaded once and reused across
    all requests, avoiding expensive reloading.
    """
    
    _instance: Optional['MedGemmaLLM'] = None
    _model = None
    _tokenizer = None
    _device = None
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(MedGemmaLLM, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize but don't load model yet (lazy loading)."""
        if Config.USE_MOCK_LLM:
            print("⚠️  Using Mock LLM (set USE_MOCK_LLM=false for real model)")
        
    def _lazy_load(self):
        """Load model only when first needed."""
        if MedGemmaLLM._model is not None:
            return  # Already loaded
        
        if Config.USE_MOCK_LLM:
            return  # Skip loading for mock mode
        
        print(f"🔄 Loading MedGemma model: {Config.MODEL_ID}")
        print("   This may take 2-5 minutes on first run...")
        
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            
            # Detect device
            MedGemmaLLM._device = Config.get_device()
            print(f"   Using device: {MedGemmaLLM._device}")
            
            # Load tokenizer
            MedGemmaLLM._tokenizer = AutoTokenizer.from_pretrained(Config.MODEL_ID)
            
            # Set padding token if not set
            if MedGemmaLLM._tokenizer.pad_token is None:
                MedGemmaLLM._tokenizer.pad_token = MedGemmaLLM._tokenizer.eos_token
            
            # Load model with appropriate dtype
            # Use bfloat16 for better numerical stability on compatible hardware
            if MedGemmaLLM._device == "cuda" and torch.cuda.is_bf16_supported():
                dtype = torch.bfloat16
                print("   Using bfloat16 for better stability")
            elif MedGemmaLLM._device != "cpu":
                dtype = torch.float16
                print("   Using float16")
            else:
                dtype = torch.float32
                print("   Using float32 (CPU)")
            
            MedGemmaLLM._model = AutoModelForCausalLM.from_pretrained(
                Config.MODEL_ID,
                torch_dtype=dtype,
                device_map={"": MedGemmaLLM._device} if MedGemmaLLM._device != "cpu" else None,
                low_cpu_mem_usage=True
            )
            
            if MedGemmaLLM._device == "cpu":
                MedGemmaLLM._model = MedGemmaLLM._model.to("cpu")
            
            print("✅ Model loaded successfully!")
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            print("   Falling back to mock mode...")
            Config.USE_MOCK_LLM = True
    
    def _format_observations(self, observations: Dict) -> str:
        """Format observations in readable text, not JSON."""
        text = "=== PATIENT DATA ===\n\n"
        
        # EHR
        if 'EHR' in observations:
            ehr = observations['EHR']
            demo = ehr.get('demographics', {})
            text += f"Patient: {demo.get('age')}yo {demo.get('gender')}\n"
            conditions = [c.get('name', '') for c in ehr.get('conditions', [])]
            text += f"Conditions: {', '.join(conditions)}\n"
            vitals = ehr.get('vitals', {})
            text += f"Vitals: BP {vitals.get('bp')}, HR {vitals.get('hr')}\n\n"
        
        # LABS
        if 'LABS' in observations:
            labs = observations['LABS']
            text += "Labs:\n"
            for lab in labs.get('results', [])[:8]:
                text += f"  {lab.get('test')}: {lab.get('value')} {lab.get('unit')} ({lab.get('status')})\n"
            text += "\n"
        
        # MEDS
        if 'MEDS' in observations:
            meds = observations['MEDS']
            active = [m.get('name') for m in meds.get('active', [])]
            text += f"Medications: {', '.join(active[:5])}\n\n"
        
        # DDI
        if 'DDI' in observations and observations['DDI']:
            text += f"Drug Interactions: {len(observations['DDI'])} identified\n\n"
        
        text += "=== END DATA ===\n"
        return text
    
    def synthesize(self, system_prompt: str, user_prompt: str, observations: Dict) -> str:
        """
        Generate clinical summary from observations.
        
        Args:
            system_prompt: System instructions for the model
            user_prompt: User query (patient_id and complaint)
            observations: Dictionary of tool observations
            
        Returns:
            Generated clinical summary text
        """
        if Config.USE_MOCK_LLM:
            mock = MockLLM()
            return mock.synthesize(system_prompt, user_prompt, observations)
        
        # Lazy load model
        self._lazy_load()
        
        if MedGemmaLLM._model is None:
            # Fallback if loading failed
            mock = MockLLM()
            return mock.synthesize(system_prompt, user_prompt, observations)
        
        try:
            # Build context with observations in readable format
            obs_summary = self._format_observations(observations)
            context = f"{system_prompt}\n\n{obs_summary}\n\n{user_prompt}\n\nGenerate clinical summary:"
            
            # Tokenize with shorter context for MPS compatibility
            # MPS has 4GB temp array limit, so reduce context length
            max_ctx_length = 2048 if MedGemmaLLM._device == "mps" else 4096
            inputs = MedGemmaLLM._tokenizer(
                context,
                return_tensors="pt",
                truncation=True,
                max_length=max_ctx_length
            ).to(MedGemmaLLM._device)
            
            # Generate with MedGemma
            print("   Generating with MedGemma...")
            with torch.no_grad():
                outputs = MedGemmaLLM._model.generate(
                    **inputs,
                    max_new_tokens=500,  # Enough for complete summary
                    do_sample=False,  # Greedy = most consistent
                    pad_token_id=MedGemmaLLM._tokenizer.pad_token_id or MedGemmaLLM._tokenizer.eos_token_id,
                    eos_token_id=MedGemmaLLM._tokenizer.eos_token_id
                )
            
            # Decode and extract
            full_text = MedGemmaLLM._tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Simple extraction: split after prompt, clean up code blocks
            if "Generate clinical summary:" in full_text:
                response = full_text.split("Generate clinical summary:")[-1].strip()
            else:
                response = full_text
            
            # Remove code block markers if present
            response = response.replace("```", "").strip()
            
            # If empty or too short, something went wrong
            if len(response) < 100:
                print(f"⚠️  Short response ({len(response)} chars), check output")
            
            return response
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error during synthesis: {error_msg}")
            
            # Provide helpful error message
            if "probability" in error_msg.lower() or "nan" in error_msg.lower():
                return (
                    f"❌ Model numerical instability detected.\n\n"
                    f"**Error:** {error_msg}\n\n"
                    f"**Quick fix:** Try using Mock mode:\n"
                    f"- Toggle 'Use Mock LLM' in the sidebar, or\n"
                    f"- Set environment variable: `export USE_MOCK_LLM=true`\n\n"
                    f"**For production:** This may indicate:\n"
                    f"- Insufficient GPU memory\n"
                    f"- Model compatibility issues\n"
                    f"- Try using CPU mode or a different model variant"
                )
            else:
                return f"❌ Error during synthesis: {error_msg}\n\nPlease check logs and model configuration."

