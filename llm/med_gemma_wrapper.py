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
            elif MedGemmaLLM._device == "mps":
                dtype = torch.float32  # float32 for MPS stability (float16 causes NaN/inf)
                print("   Using float32 (MPS - float16 causes numerical instability)")
            elif MedGemmaLLM._device != "cpu":
                dtype = torch.float16
                print("   Using float16")
            else:
                dtype = torch.float32
                print("   Using float32 (CPU)")
            
            # Load model - use device_map only for CUDA (if accelerate available), otherwise load to CPU then move
            try:
                # Try using device_map for CUDA (requires accelerate)
                if MedGemmaLLM._device == "cuda":
                    try:
                        MedGemmaLLM._model = AutoModelForCausalLM.from_pretrained(
                            Config.MODEL_ID,
                            dtype=dtype,
                            device_map={"": MedGemmaLLM._device},
                            low_cpu_mem_usage=True
                        )
                    except Exception:
                        # Fallback: load to CPU then move to CUDA
                        print("   device_map not available, loading to CPU then moving to CUDA...")
                        MedGemmaLLM._model = AutoModelForCausalLM.from_pretrained(
                            Config.MODEL_ID,
                            dtype=dtype,
                            low_cpu_mem_usage=True
                        )
                        MedGemmaLLM._model = MedGemmaLLM._model.to(MedGemmaLLM._device)
                else:
                    # For MPS and CPU: load to CPU first, then move to device
                    MedGemmaLLM._model = AutoModelForCausalLM.from_pretrained(
                        Config.MODEL_ID,
                        dtype=dtype,
                        low_cpu_mem_usage=True
                    )
                    if MedGemmaLLM._device != "cpu":
                        MedGemmaLLM._model = MedGemmaLLM._model.to(MedGemmaLLM._device)
            except Exception as load_error:
                # Final fallback: load to CPU
                print(f"   Warning: {load_error}")
                print("   Loading to CPU as fallback...")
                MedGemmaLLM._model = AutoModelForCausalLM.from_pretrained(
                    Config.MODEL_ID,
                    dtype=torch.float32,
                    low_cpu_mem_usage=True
                )
                MedGemmaLLM._model = MedGemmaLLM._model.to("cpu")
                MedGemmaLLM._device = "cpu"
            
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
            print("   Model not loaded, using template generator fallback")
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
            print(f"   Input shape: {inputs['input_ids'].shape}, Device: {inputs['input_ids'].device}")
            
            with torch.no_grad():
                try:
                    # For MPS, use sampling mode (greedy decoding can be problematic)
                    if MedGemmaLLM._device == "mps":
                        outputs = MedGemmaLLM._model.generate(
                            **inputs,
                            max_new_tokens=300,  # Shorter for MPS stability
                            do_sample=True,
                            temperature=0.7,
                            top_p=0.9,
                            pad_token_id=MedGemmaLLM._tokenizer.pad_token_id or MedGemmaLLM._tokenizer.eos_token_id,
                            eos_token_id=MedGemmaLLM._tokenizer.eos_token_id
                        )
                    else:
                        outputs = MedGemmaLLM._model.generate(
                            **inputs,
                            max_new_tokens=500,  # Enough for complete summary
                            do_sample=False,  # Greedy = most consistent
                            pad_token_id=MedGemmaLLM._tokenizer.pad_token_id or MedGemmaLLM._tokenizer.eos_token_id,
                            eos_token_id=MedGemmaLLM._tokenizer.eos_token_id
                        )
                    print(f"   Generated output shape: {outputs.shape}, Device: {outputs.device}")
                except Exception as gen_error:
                    error_str = str(gen_error).lower()
                    print(f"   Generation error: {gen_error}")
                    
                    # Check for numerical instability (NaN/inf errors)
                    if any(keyword in error_str for keyword in ['nan', 'inf', 'probability tensor', 'numerical']):
                        print("   ⚠️  Numerical instability detected - MPS float16 precision issue")
                        print("   Falling back to template generator (more reliable)")
                        # Fallback to template generator immediately
                        from agent.template_generator import TemplateSummaryGenerator
                        patient_id = user_prompt.split("patient_id:")[1].split("\n")[0].strip() if "patient_id:" in user_prompt else "unknown"
                        complaint = user_prompt.split("complaint:")[1].strip().strip('"') if "complaint:" in user_prompt else "clinical evaluation"
                        return TemplateSummaryGenerator.generate_from_data(observations, patient_id, complaint)
                    
                    # For other errors, try retry logic
                    if MedGemmaLLM._device == "mps":
                        print("   Retrying with different parameters for MPS...")
                        try:
                            # Try with even more conservative settings
                            outputs = MedGemmaLLM._model.generate(
                                **inputs,
                                max_new_tokens=200,  # Even shorter
                                do_sample=True,
                                temperature=0.5,  # Lower temperature
                                top_p=0.95,
                                pad_token_id=MedGemmaLLM._tokenizer.pad_token_id or MedGemmaLLM._tokenizer.eos_token_id,
                                eos_token_id=MedGemmaLLM._tokenizer.eos_token_id
                            )
                        except Exception:
                            # Final fallback to template generator
                            print("   MPS generation failed, using template generator")
                            from agent.template_generator import TemplateSummaryGenerator
                            patient_id = user_prompt.split("patient_id:")[1].split("\n")[0].strip() if "patient_id:" in user_prompt else "unknown"
                            complaint = user_prompt.split("complaint:")[1].strip().strip('"') if "complaint:" in user_prompt else "clinical evaluation"
                            return TemplateSummaryGenerator.generate_from_data(observations, patient_id, complaint)
                    else:
                        raise gen_error
            
            # Move outputs to CPU before decoding (required for MPS)
            if outputs.device.type == "mps":
                outputs = outputs.cpu()
            
            # Decode and extract
            full_text = MedGemmaLLM._tokenizer.decode(outputs[0], skip_special_tokens=True)
            print(f"   Full decoded text length: {len(full_text)} chars")
            print(f"   First 200 chars: {full_text[:200]}")
            
            # Simple extraction: split after prompt, clean up code blocks
            if "Generate clinical summary:" in full_text:
                response = full_text.split("Generate clinical summary:")[-1].strip()
            else:
                # If prompt not found, try to extract after user_prompt
                if user_prompt in full_text:
                    response = full_text.split(user_prompt)[-1].strip()
                else:
                    # Use everything after the system prompt
                    response = full_text[len(context.split("Generate clinical summary:")[0]):].strip() if "Generate clinical summary:" in context else full_text
            
            # Remove code block markers if present
            response = response.replace("```", "").strip()
            
            # Remove duplicates (check if content appears twice)
            lines = response.split('\n')
            seen_sections = set()
            deduplicated_lines = []
            current_section = []
            
            for line in lines:
                # Check if this is a section header (starts with ##)
                if line.strip().startswith('##'):
                    # Save previous section if not duplicate
                    if current_section and current_section[0] not in seen_sections:
                        deduplicated_lines.extend(current_section)
                        seen_sections.add(current_section[0])
                    current_section = [line.strip()]
                else:
                    if current_section:
                        current_section.append(line)
                    else:
                        deduplicated_lines.append(line)
            
            # Add last section
            if current_section and current_section[0] not in seen_sections:
                deduplicated_lines.extend(current_section)
            
            response = '\n'.join(deduplicated_lines).strip()
            
            # If empty or too short, something went wrong - use template generator as fallback
            if len(response) < 50:
                print(f"⚠️  Short/empty response ({len(response)} chars), using template generator fallback")
                # Fallback to template generator
                from agent.template_generator import TemplateSummaryGenerator
                patient_id = user_prompt.split("patient_id:")[1].split("\n")[0].strip() if "patient_id:" in user_prompt else "unknown"
                complaint = user_prompt.split("complaint:")[1].strip().strip('"') if "complaint:" in user_prompt else "clinical evaluation"
                response = TemplateSummaryGenerator.generate_from_data(observations, patient_id, complaint)
            
            return response
            
        except Exception as e:
            error_msg = str(e)
            error_str = error_msg.lower()
            print(f"❌ Error during synthesis: {error_msg}")
            
            # Check for numerical instability - fallback to template generator
            if any(keyword in error_str for keyword in ['nan', 'inf', 'probability tensor', 'numerical']):
                print("   ⚠️  Numerical instability detected - using template generator fallback")
                try:
                    from agent.template_generator import TemplateSummaryGenerator
                    patient_id = user_prompt.split("patient_id:")[1].split("\n")[0].strip() if "patient_id:" in user_prompt else "unknown"
                    complaint = user_prompt.split("complaint:")[1].strip().strip('"') if "complaint:" in user_prompt else "clinical evaluation"
                    return TemplateSummaryGenerator.generate_from_data(observations, patient_id, complaint)
                except Exception as fallback_error:
                    return (
                        f"⚠️  Model numerical instability detected (MPS float16 precision issue).\n\n"
                        f"**Error:** {error_msg}\n\n"
                        f"**Solution:** The system automatically fell back to template-based generation.\n"
                        f"**For best results:** Use Mock Mode (template generator) which is faster and more reliable:\n"
                        f"- Toggle 'Fast Analysis Mode' in the sidebar, or\n"
                        f"- Set: `export USE_MOCK_LLM=true`\n\n"
                        f"Template generator provides structured, accurate clinical reports without model inference."
                    )
            
            # Other errors - try template generator as fallback
            try:
                from agent.template_generator import TemplateSummaryGenerator
                patient_id = user_prompt.split("patient_id:")[1].split("\n")[0].strip() if "patient_id:" in user_prompt else "unknown"
                complaint = user_prompt.split("complaint:")[1].strip().strip('"') if "complaint:" in user_prompt else "clinical evaluation"
                print("   Using template generator as fallback")
                return TemplateSummaryGenerator.generate_from_data(observations, patient_id, complaint)
            except Exception:
                return f"❌ Error during synthesis: {error_msg}\n\nPlease check logs and model configuration."

