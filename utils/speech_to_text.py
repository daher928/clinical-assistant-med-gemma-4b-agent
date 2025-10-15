"""
Speech-to-text using Google Gemini API.
"""
import google.generativeai as genai
import tempfile
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class GeminiSpeechToText:
    """Convert audio to text using Gemini API."""
    
    def __init__(self, api_key: str):
        """Initialize with Gemini API key."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')  # Use stable model
    
    def transcribe_audio(self, audio_bytes: bytes) -> str:
        """
        Transcribe audio bytes to text using Gemini.
        
        Args:
            audio_bytes: Audio data in bytes (WAV format)
            
        Returns:
            Transcribed text
        """
        try:
            import base64
            
            # Convert audio to base64 for direct API call
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            # Create inline data part
            audio_part = {
                "inline_data": {
                    "mime_type": "audio/wav",
                    "data": audio_b64
                }
            }
            
            # Transcribe with Gemini (direct audio input)
            prompt = "Transcribe this audio recording of a patient's chief complaint. Return only the transcribed text, no explanations."
            response = self.model.generate_content([prompt, audio_part])
            
            return response.text.strip()
            
        except Exception as e:
            print(f"❌ Speech-to-text error: {e}")
            return f"Error: Could not transcribe audio - {str(e)}"


# Initialize with API key from environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_stt = None

try:
    if GEMINI_API_KEY:
        gemini_stt = GeminiSpeechToText(GEMINI_API_KEY)
    else:
        print("⚠️  GEMINI_API_KEY not found - audio transcription disabled")
except Exception as e:
    print(f"⚠️  Could not initialize Gemini API: {e}")
    print("   Audio transcription feature will be disabled")
    gemini_stt = None


def transcribe_audio_bytes(audio_bytes: bytes) -> str:
    """
    Convenience function to transcribe audio.
    
    Args:
        audio_bytes: Audio data in bytes
        
    Returns:
        Transcribed text
    """
    if gemini_stt is None:
        return "Audio transcription unavailable. Please add valid GEMINI_API_KEY to .env file."
    
    return gemini_stt.transcribe_audio(audio_bytes)

