"""
Speech-to-text using Google Gemini API.
"""
import google.generativeai as genai
import tempfile
import os


class GeminiSpeechToText:
    """Convert audio to text using Gemini API."""
    
    def __init__(self, api_key: str):
        """Initialize with Gemini API key."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def transcribe_audio(self, audio_bytes: bytes) -> str:
        """
        Transcribe audio bytes to text using Gemini.
        
        Args:
            audio_bytes: Audio data in bytes (WAV format)
            
        Returns:
            Transcribed text
        """
        try:
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
                temp_audio.write(audio_bytes)
                temp_path = temp_audio.name
            
            # Upload file to Gemini
            audio_file = genai.upload_file(temp_path)
            
            # Transcribe with Gemini
            prompt = "Transcribe this audio recording of a patient's chief complaint. Return only the transcribed text, no explanations."
            response = self.model.generate_content([prompt, audio_file])
            
            # Clean up
            os.unlink(temp_path)
            genai.delete_file(audio_file.name)
            
            return response.text.strip()
            
        except Exception as e:
            print(f"❌ Speech-to-text error: {e}")
            return f"Error: Could not transcribe audio - {str(e)}"


# Initialize with provided API key
GEMINI_API_KEY = "AIzaSyDTPD-Ak5trwvjZ0viHVvu8JneLthgMHA4"
gemini_stt = GeminiSpeechToText(GEMINI_API_KEY)


def transcribe_audio_bytes(audio_bytes: bytes) -> str:
    """
    Convenience function to transcribe audio.
    
    Args:
        audio_bytes: Audio data in bytes
        
    Returns:
        Transcribed text
    """
    return gemini_stt.transcribe_audio(audio_bytes)

